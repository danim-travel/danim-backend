from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import ActionEnum, CategoryEnum, PresignedUrlView, SuffixEnum
from apps.core.utils.pagination import paginate
from apps.supports.serializers import (
    FAQFeedbackSerializer,
    InquiryCreateSerializer,
    InquiryDetailSerializer,
    InquiryListSerializer,
)
from apps.supports.services import (
    create_faq_feedback,
    create_inquiry,
    delete_my_inquiry,
    get_faq_categories,
    get_faq_detail,
    get_faqs_by_category,
    get_my_inquiries,
    get_my_inquiry_detail,
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
    """POST /api/v1/supports/faqs/{faq_id}/feedback — "해결되셨나요?" 응답

    무인증 쓰기 엔드포인트라 IP/유저 기준 rate limit으로 통계 오염을 방어한다
    (로그인 사용자의 중복은 서비스 레이어 upsert + DB 유니크 제약이 담당).
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "faq_feedback"

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


class InquiryListCreateView(APIView):
    """POST/GET /api/v1/supports/inquiries — 1:1 문의 등록 / 내 문의 목록"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["고객센터"],
        summary="1:1 문의 등록",
        request=InquiryCreateSerializer,
        responses={201: InquiryDetailSerializer},
    )
    def post(self, request: Request) -> Response:
        serializer = InquiryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inquiry = create_inquiry(cast(User, request.user), serializer.validated_data)
        return Response(
            InquiryDetailSerializer(inquiry).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["고객센터"],
        summary="내 문의 목록 조회",
        responses={200: InquiryListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        queryset = get_my_inquiries(cast(User, request.user))
        return paginate(queryset, request, InquiryListSerializer)


class InquiryDetailView(APIView):
    """GET/DELETE /api/v1/supports/inquiries/{inquiry_id} — 내 문의 상세 + 답변 / 삭제"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["고객센터"],
        summary="내 문의 상세 조회",
        responses={200: InquiryDetailSerializer},
    )
    def get(self, request: Request, inquiry_id: str) -> Response:
        return Response(get_my_inquiry_detail(inquiry_id, cast(User, request.user)))

    @extend_schema(
        tags=["고객센터"],
        summary="내 문의 삭제 (미답변 상태에서만)",
        responses={204: None},
    )
    def delete(self, request: Request, inquiry_id: str) -> Response:
        delete_my_inquiry(inquiry_id, cast(User, request.user))
        return Response(status=status.HTTP_204_NO_CONTENT)


class InquiryPresignedUrlView(PresignedUrlView):
    """POST /api/v1/supports/inquiries/presigned-url — 문의 첨부 이미지 업로드 URL

    category=inquiry로 고정 발급한다. 문의 저장 시 같은 카테고리인지 재검증하므로
    (InquiryCreateSerializer.validate_image_key) 다른 카테고리 key는 붙지 않는다.
    """

    permission_classes: list[type[Any]] = [IsAuthenticated]
    action = ActionEnum.UPLOAD
    category = CategoryEnum.INQUIRY
    suffix = SuffixEnum.NONE

    @extend_schema(tags=["고객센터"], summary="문의 이미지 업로드 URL 발급")
    def post(self, request: Request) -> Response:
        return super().post(request)
