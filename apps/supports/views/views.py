from typing import cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception import ValidationException
from apps.supports.serializers import FAQFeedbackSerializer
from apps.supports.services import (
    create_faq_feedback,
    get_faq_categories,
    get_faq_detail,
    get_faqs_by_category,
)
from apps.users.models import User


class FAQCategoryListView(APIView):
    """GET /api/v1/supports/faqs/categories — FAQ 카테고리 목록 (챗봇 첫 화면)"""

    permission_classes = [AllowAny]

    @extend_schema(tags=["고객센터"], summary="FAQ 카테고리 목록 조회")
    def get(self, request: Request) -> Response:
        return Response({"categories": get_faq_categories()})


class FAQListView(APIView):
    """GET /api/v1/supports/faqs?category={id} — 카테고리별 질문 목록"""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["고객센터"],
        summary="카테고리별 질문 목록 조회",
        parameters=[
            OpenApiParameter(
                name="category", type=str, required=True, description="카테고리 ID(ULID)"
            )
        ],
    )
    def get(self, request: Request) -> Response:
        category_id = request.query_params.get("category")
        if not category_id:
            raise ValidationException("category는 필수입니다.")
        return Response({"faqs": get_faqs_by_category(category_id)})


class FAQDetailView(APIView):
    """GET /api/v1/supports/faqs/{faq_id} — FAQ 답변 조회"""

    permission_classes = [AllowAny]

    @extend_schema(tags=["고객센터"], summary="FAQ 답변 조회")
    def get(self, request: Request, faq_id: str) -> Response:
        return Response(get_faq_detail(faq_id))


class FAQFeedbackView(APIView):
    """POST /api/v1/supports/faqs/{faq_id}/feedback — "해결되셨나요?" 응답"""

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["고객센터"],
        summary="FAQ 해결 피드백 등록",
        request=FAQFeedbackSerializer,
    )
    def post(self, request: Request, faq_id: str) -> Response:
        serializer = FAQFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, request.user) if request.user.is_authenticated else None
        create_faq_feedback(faq_id, serializer.validated_data["is_helpful"], user)
        return Response(
            {"detail": "피드백이 등록되었습니다."}, status=status.HTTP_201_CREATED
        )
