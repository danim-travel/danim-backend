from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.notifications.serializers import (
    NotificationListSerializer,
    NotificationSwaggerSerializer,
)

notification_list_schema = extend_schema(
    parameters=[NotificationSwaggerSerializer],
    responses={
        200: NotificationListSerializer,
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
        ),
    },
    tags=["notifications"],
    summary="알림 목록 조회 api",
)
