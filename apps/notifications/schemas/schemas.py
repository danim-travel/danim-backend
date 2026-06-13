from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.notifications.serializers import (
    NotificationDeleteSerializer,
    NotificationReadSerializer,
)

notification_read_schema = extend_schema(
    responses={
        200: NotificationReadSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="해당 알림을 찾지 못했습니다."),
    },
    tags=["notifications"],
    summary="알림 개별 읽음 처리 api",
)

notification_delete_schema = extend_schema(
    responses={
        200: NotificationDeleteSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="해당 알림을 찾지 못했습니다."),
    },
    tags=["notifications"],
    summary="알림 개별 삭제 처리 api",
)
