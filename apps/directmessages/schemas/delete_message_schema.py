from drf_spectacular.utils import OpenApiResponse, extend_schema

delete_message_schema = extend_schema(
    tags=["direct-messages"],
    summary="메시지 삭제",
    responses={
        204: OpenApiResponse(description="메시지 삭제 성공"),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        403: OpenApiResponse(description="본인이 보낸 메시지만 삭제할 수 있습니다."),
        404: OpenApiResponse(description="대화방 또는 메시지를 찾을 수 없습니다."),
    },
)
