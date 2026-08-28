from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import validate_attach_key
from apps.supports.models import (
    FAQ,
    FAQCategory,
    Inquiry,
    InquiryAnswer,
    PendingInquiryAttachmentDeletion,
)


class FAQCategorySerializer(serializers.ModelSerializer):
    """카테고리 목록 (챗봇 첫 화면 버튼)"""

    category_id = serializers.CharField(source="id")

    class Meta:
        model = FAQCategory
        fields = ["category_id", "name", "order"]


class FAQListSerializer(serializers.ModelSerializer):
    """카테고리별 질문 목록 (답변은 상세에서)"""

    faq_id = serializers.CharField(source="id")

    class Meta:
        model = FAQ
        fields = ["faq_id", "question", "order"]


class FAQDetailSerializer(serializers.ModelSerializer):
    """질문 선택 시 답변 상세"""

    faq_id = serializers.CharField(source="id")

    class Meta:
        model = FAQ
        fields = ["faq_id", "question", "answer", "updated_at"]


class FAQFeedbackSerializer(serializers.Serializer):
    """ "해결되셨나요?" 응답"""

    is_helpful = serializers.BooleanField(required=True)


class InquiryCreateSerializer(serializers.ModelSerializer):
    """1:1 문의 등록 요청.

    img_key는 presigned로 발급받은 문의용 key만 허용한다 — 무검증이면 DM 등
    비공개 문맥의 key를 붙여 다른 경로로 재노출할 수 있다(교차 카테고리 세탁).
    """

    class Meta:
        model = Inquiry
        fields = ["category", "title", "content", "img_key"]

    def validate_img_key(self, value: str | None) -> str | None:
        # `value in (None, "")`로 쓰면 mypy가 str로 좁히지 못해 아래 호출이 걸린다.
        if not value:
            return None
        validate_attach_key(value, CategoryEnum.INQUIRY)

        # **key 재사용을 두 검사의 합집합으로 막는다. 둘은 대안이 아니라 상호보완이다.**
        #
        #   구간                 Inquiry 검사        대장 검사
        #   삭제 트랜잭션 커밋 전   A가 보인다 → 막음    아직 안 보임(READ COMMITTED)
        #   삭제 트랜잭션 커밋 후   A가 사라져 못 봄     행이 보인다 → 막음
        #
        # 대장만 두면(5차 리뷰 HIGH) "살아 있는 두 문의가 같은 key를 공유"하는 상태가
        # 만들어진다. 상세 응답이 `image.key`를 그대로 돌려주므로 재제출만으로 도달
        # 가능하다. 그 상태에서 A를 지우면 파기 태스크가 B의 참조를 보고 **재시도 없이
        # 보류**하고, 대장 행과 S3 객체가 함께 남는다. B에 답변이 달리면 사용자는 409로
        # B도 못 지워 회수 수단이 사라진다.
        #
        # Inquiry 검사만 두면 반대로 커밋 후 구간이 열린다 — A가 이미 없고 B는 아직
        # 없어 이 검사와 파기 태스크의 검사가 **같은 False를 본다**(4차 리뷰).
        #
        # 정상 사용에는 제약이 없다 — 첨부는 presigned로 매번 새 key를 발급받는다.
        if Inquiry.objects.filter(img_key=value).exists():
            raise serializers.ValidationError("이미 사용된 이미지입니다.")
        if PendingInquiryAttachmentDeletion.objects.filter(key=value).exists():
            raise serializers.ValidationError("파기 예약된 이미지입니다.")
        return value


class InquiryListSerializer(serializers.ModelSerializer):
    """내 문의 목록 — 본문·이미지는 상세에서."""

    inquiry_id = serializers.CharField(source="id")

    class Meta:
        model = Inquiry
        fields = ["inquiry_id", "category", "title", "status", "created_at"]


class InquiryAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = InquiryAnswer
        fields = ["content", "created_at"]


class InquiryImageSerializer(serializers.Serializer):
    """첨부 이미지 응답 형태(스키마 문서화 전용). 첨부가 없으면 두 값 모두 null."""

    key = serializers.CharField(allow_null=True)
    img_url = serializers.CharField(allow_null=True)


class InquiryDetailSerializer(serializers.ModelSerializer):
    """내 문의 상세 — 답변이 없으면 answer는 null.

    answer를 중첩 serializer로 직접 선언하면 안 된다. 역방향 OneToOne은 답변이 없을 때
    RelatedObjectDoesNotExist(AttributeError 상속)를 던지고, DRF는 그걸 SkipField로
    처리해 **응답에서 키 자체가 사라진다**. 프론트가 `data.answer === null`로 분기하면
    미답변 문의에서 undefined를 만나므로, 항상 키가 존재하도록 명시적으로 만든다.
    """

    inquiry_id = serializers.CharField(source="id")
    answer = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    @extend_schema_field(InquiryAnswerSerializer(allow_null=True))
    def get_answer(self, obj: Inquiry) -> dict[str, Any] | None:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return None
        return dict(InquiryAnswerSerializer(answer).data)

    @extend_schema_field(InquiryImageSerializer)
    def get_image(self, obj: Inquiry) -> dict[str, str | None]:
        """버킷이 비공개라 key만 내려주면 클라이언트가 첨부를 다시 볼 수 없다.
        형제 도메인(댓글·프로필·DM)과 같이 조회용 presigned URL을 함께 준다.
        """
        if not obj.img_key:
            return {"key": None, "img_url": None}
        return {
            "key": obj.img_key,
            "img_url": s3_svc.create_download_presigned_url(obj.img_key),
        }

    class Meta:
        model = Inquiry
        fields = [
            "inquiry_id",
            "category",
            "title",
            "content",
            "image",
            "status",
            "created_at",
            "answer",
        ]
