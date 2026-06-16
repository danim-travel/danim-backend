from drf_spectacular.utils import OpenApiResponse, extend_schema

leave_conversation_schema = extend_schema(
    tags=["direct-messages"],
    summary="대화방 나가기",
    responses={
        204: OpenApiResponse(description="대화방 나가기 성공"),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="대화방을 찾을 수 없습니다."),
    },
)
