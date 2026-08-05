from rest_framework import serializers

from apps.supports.models import FAQ, FAQCategory


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
