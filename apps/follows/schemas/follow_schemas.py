from drf_spectacular.utils import OpenApiResponse, extend_schema

follow_create_schema = extend_schema(
    responses={
        201: OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "is_followed": {"type": "boolean"},
                    "follower_count": {"type": "integer"},
                },
            }
        ),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="해당 유저를 찾을 수 없습니다."),
        409: OpenApiResponse(description="이미 팔로우 중입니다."),
    }
)
follow_delete_schema = extend_schema(
    responses={
        200: OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "is_followed": {"type": "boolean"},
                    "follower_count": {"type": "integer"},
                },
            }
        ),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="해당 유저를 찾을 수 없습니다."),
    }
)
