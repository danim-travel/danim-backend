"""FAQ 챗봇 조회/피드백 서비스.

조회 3종은 default 캐시(fail-open)를 사용한다 — FAQ는 변경이 드물고
챗봇 진입마다 호출되므로 캐시 효율이 높고, Redis 장애 시에는 예외를
삼키고 DB로 동작한다(기존 캐시 정책 참조: config/settings/base.py).
무효화는 signals/signal.py에서 admin 저장/삭제 시 수행된다.
"""

from typing import Any, cast

from django.core.cache import cache

from apps.core.exceptions.exception import NotFoundException
from apps.supports.models import FAQ, FAQCategory, FAQFeedback
from apps.supports.serializers import (
    FAQCategorySerializer,
    FAQDetailSerializer,
    FAQListSerializer,
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
    """ "해결되셨나요?" 응답 저장. 비로그인이면 user=None."""
    if not FAQ.objects.filter(
        id=faq_id, is_active=True, category__is_active=True
    ).exists():
        raise NotFoundException("존재하지 않는 FAQ입니다.")

    FAQFeedback.objects.create(faq_id=faq_id, is_helpful=is_helpful, user=user)


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
