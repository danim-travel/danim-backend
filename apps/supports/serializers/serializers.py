from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import validate_attach_key
from apps.supports.models import FAQ, FAQCategory, Inquiry, InquiryAnswer


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

    image_key는 presigned로 발급받은 문의용 key만 허용한다 — 무검증이면 DM 등
    비공개 문맥의 key를 붙여 다른 경로로 재노출할 수 있다(교차 카테고리 세탁).
    """

    class Meta:
        model = Inquiry
        fields = ["category", "title", "content", "image_key"]

    def validate_image_key(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        return validate_attach_key(value, CategoryEnum.INQUIRY)


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


class InquiryDetailSerializer(serializers.ModelSerializer):
    """내 문의 상세 — 답변이 없으면 answer는 null.

    answer를 중첩 serializer로 직접 선언하면 안 된다. 역방향 OneToOne은 답변이 없을 때
    RelatedObjectDoesNotExist(AttributeError 상속)를 던지고, DRF는 그걸 SkipField로
    처리해 **응답에서 키 자체가 사라진다**. 프론트가 `data.answer === null`로 분기하면
    미답변 문의에서 undefined를 만나므로, 항상 키가 존재하도록 명시적으로 만든다.
    """

    inquiry_id = serializers.CharField(source="id")
    answer = serializers.SerializerMethodField()

    @extend_schema_field(InquiryAnswerSerializer(allow_null=True))
    def get_answer(self, obj: Inquiry) -> dict[str, Any] | None:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return None
        return dict(InquiryAnswerSerializer(answer).data)

    class Meta:
        model = Inquiry
        fields = [
            "inquiry_id",
            "category",
            "title",
            "content",
            "image_key",
            "status",
            "created_at",
            "answer",
        ]
