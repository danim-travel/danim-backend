from drf_spectacular.utils import OpenApiResponse, extend_schema

follow_create_schema = extend_schema(
    responses={
        200: OpenApiResponse(
            response={
                "type": "object",
                "properties": {
                    "is_followed": {"type": "boolean"},
                    "follower_count": {"type": "integer"},
                },
            }
        )
    }
)
