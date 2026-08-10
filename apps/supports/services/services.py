"""FAQ 챗봇 조회/피드백 서비스.

조회 3종은 default 캐시(fail-open)를 사용한다 — FAQ는 변경이 드물고
챗봇 진입마다 호출되므로 캐시 효율이 높고, Redis 장애 시에는 예외를
삼키고 DB로 동작한다(기존 캐시 정책 참조: config/settings/base.py).
무효화는 signals/signal.py에서 admin 저장/삭제 시 수행된다.
"""

from typing import Any, cast

from django.core.cache import cache
from django.db.models import QuerySet

from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.supports.models import FAQ, FAQCategory, FAQFeedback, Inquiry, InquiryStatus
from apps.supports.serializers import (
    FAQCategorySerializer,
    FAQDetailSerializer,
    FAQListSerializer,
    InquiryDetailSerializer,
)
from apps.users.models import User

FAQ_CACHE_TTL = 60 * 60  # 1시간 — 무효화가 주 수단이고 TTL은 안전망

CATEGORIES_CACHE_KEY = "supports:faqs:categories"
FAQ_LIST_CACHE_KEY = "supports:faqs:list:{category_id}"
FAQ_DETAIL_CACHE_KEY = "supports:faqs:detail:{faq_id}"


def get_faq_categories() -> list[dict[str, Any]]:
    """활성 카테고리 목록 (챗봇 첫 화면 버튼)"""
    cached = cache.get(CATEGORIES_CACHE_KEY)
    if cached is not None:
        return cached

    categories = FAQCategory.objects.filter(is_active=True)
    data = [dict(item) for item in FAQCategorySerializer(categories, many=True).data]
    cache.set(CATEGORIES_CACHE_KEY, data, FAQ_CACHE_TTL)
    return data


def get_faqs_by_category(category_id: str) -> list[dict[str, Any]]:
    """카테고리의 활성 질문 목록. 카테고리가 없거나 비활성이면 404."""
    key = FAQ_LIST_CACHE_KEY.format(category_id=category_id)
    cached = cache.get(key)
    if cached is not None:
        return cached

    if not FAQCategory.objects.filter(id=category_id, is_active=True).exists():
        raise NotFoundException("존재하지 않는 카테고리입니다.")

    faqs = FAQ.objects.filter(category_id=category_id, is_active=True)
    data = [dict(item) for item in FAQListSerializer(faqs, many=True).data]
    cache.set(key, data, FAQ_CACHE_TTL)
    return data


def get_faq_detail(faq_id: str) -> dict[str, Any]:
    """질문의 답변 상세. 질문이 없거나 (본인/카테고리) 비활성이면 404."""
    key = FAQ_DETAIL_CACHE_KEY.format(faq_id=faq_id)
    cached = cache.get(key)
    if cached is not None:
        return cached

    faq = (
        FAQ.objects.filter(id=faq_id, is_active=True, category__is_active=True)
        .only("id", "question", "answer", "updated_at")
        .first()
    )
    if faq is None:
        raise NotFoundException("존재하지 않는 FAQ입니다.")

    data = dict(FAQDetailSerializer(faq).data)
    cache.set(key, data, FAQ_CACHE_TTL)
    return data


def create_faq_feedback(faq_id: str, is_helpful: bool, user: User | None) -> None:
    """ "해결되셨나요?" 응답 저장. 비로그인이면 user=None.

    로그인 사용자는 FAQ당 1응답(재응답 시 갱신)으로 통계 중복을 막는다.
    익명은 식별자가 없어 중복 제약이 불가능하므로 뷰의 rate limit으로 방어.
    """
    if not FAQ.objects.filter(
        id=faq_id, is_active=True, category__is_active=True
    ).exists():
        raise NotFoundException("존재하지 않는 FAQ입니다.")

    if user is not None:
        FAQFeedback.objects.update_or_create(
            faq_id=faq_id, user=user, defaults={"is_helpful": is_helpful}
        )
    else:
        FAQFeedback.objects.create(faq_id=faq_id, is_helpful=is_helpful, user=None)


def create_inquiry(user: User, validated_data: dict[str, Any]) -> Inquiry:
    """1:1 문의 등록. 상태는 모델 기본값(PENDING)에서 시작한다."""
    return Inquiry.objects.create(user=user, **validated_data)


def get_my_inquiries(user: User) -> QuerySet[Inquiry]:
    """내 문의 목록. 캐시하지 않는다 — 사용자별 데이터라 적중률이 낮고,
    답변 직후 목록에 옛 상태가 보이면 알림과 화면이 어긋난다.
    """
    return Inquiry.objects.filter(user=user)


def get_my_inquiry_detail(inquiry_id: str, user: User) -> dict[str, Any]:
    """내 문의 상세 + 답변.

    조건: 본인 문의만 조회할 수 있다. 남의 문의는 403이 아니라 404로 응답한다 —
        403은 "그 ID의 문의가 존재한다"를 알려줘 ID 대입으로 존재 여부를 캐낼 수 있다.
    """
    inquiry = (
        Inquiry.objects.filter(id=inquiry_id, user=user).select_related("answer").first()
    )
    if inquiry is None:
        raise NotFoundException("존재하지 않는 문의입니다.")
    return dict(InquiryDetailSerializer(inquiry).data)


def delete_my_inquiry(inquiry_id: str, user: User) -> None:
    """내 문의 삭제.

    기능: 잘못 올렸거나 개인정보를 적어 지우고 싶은 경우를 위한 경로다. 수정은
        제공하지 않는다 — 운영진이 이미 읽고 처리 중인 문의의 본문이 바뀌면
        답변과 질문이 어긋난다. 지우고 다시 쓰는 편이 명확하다.
    조건: 본인 문의이면서 아직 PENDING일 때만 지울 수 있다. 상태로 판정하는 이유는
        운영진이 스팸을 답변 없이 CLOSED로 정리한 건도 이미 분류가 끝난 것이라
        사용자가 되돌릴 대상이 아니기 때문이다.
    예외: 남의 문의는 404(get_my_inquiry_detail과 같은 이유), 이미 처리된 문의는 409.

    첨부 이미지(S3 객체)는 함께 지우지 않는다 — 이 프로젝트의 어느 도메인도
    레코드 삭제 시 S3 객체를 지우지 않으며(수명주기 정책 영역), 문의만 예외로
    두면 동작이 불규칙해진다.

    **판정을 파이썬이 아니라 DELETE의 WHERE에 둔다.** `first()`로 읽어 상태를 보고
    조건 없는 `delete()`를 부르면, SELECT와 DELETE 사이에 운영진의 답변 저장이
    커밋됐을 때 그 답변까지 CASCADE로 지워진다. ATOMIC_REQUESTS가 꺼져 있어 뷰
    전체를 감싸는 트랜잭션도 없다. 게다가 예약된 알림 태스크는 행이 사라진 것을
    warning으로만 남기고 끝나 소실이 무증상이 된다(1차 리뷰 MEDIUM).
    """
    deleted = (
        Inquiry.objects.filter(
            id=inquiry_id, user=user, status=InquiryStatus.PENDING
        ).delete()[1]
    ).get(Inquiry._meta.label, 0)
    if deleted:
        return
    # 0건이면 "없어서"인지 "이미 처리돼서"인지 갈라 응답만 정한다. 이 조회는 위
    # DELETE와 별개 시점이라 경합에 노출되지만, 어느 쪽으로 갈리든 결과는 "지울 수
    # 없다"로 같아서 해가 없다.
    if Inquiry.objects.filter(id=inquiry_id, user=user).exists():
        raise ConflictException("이미 처리된 문의는 삭제할 수 없습니다.")
    raise NotFoundException("존재하지 않는 문의입니다.")


def invalidate_faq_cache() -> None:
    """FAQ 캐시 전체 무효화.

    카테고리 이동·카테고리 비활성화(하위 질문 상세까지 숨김) 같은 경계
    케이스를 개별 키 계산 없이 확실하게 덮기 위해 전부 비운다 — FAQ 데이터는
    작고 무효화는 admin 저장 시에만 일어나므로 비용이 무시할 수준이다.
    (delete_pattern은 django-redis 전용 API — 프로젝트 캐시 백엔드 고정)
    """
    cache.delete(CATEGORIES_CACHE_KEY)
    # delete_pattern은 django-redis 전용이라 BaseCache 타입에 없음 — Any로 캐스팅
    redis_cache = cast(Any, cache)
    redis_cache.delete_pattern(FAQ_LIST_CACHE_KEY.format(category_id="*"))
    redis_cache.delete_pattern(FAQ_DETAIL_CACHE_KEY.format(faq_id="*"))
