from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.notifications.serializers import (
    NotificationListReadSwaggerSerializer,
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

notification_read_all_schema = extend_schema(
    responses={
        200: NotificationListReadSwaggerSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
    tags=["notifications"],
    summary="전체 알림 읽음 처리 api",
)
notification_delete_all_schema = extend_schema(
    responses={
        200: NotificationListReadSwaggerSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
    tags=["notifications"],
    summary="전체 알림 삭제 처리 api",
)
