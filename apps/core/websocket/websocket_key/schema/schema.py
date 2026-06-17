from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers


class SocketKeySerializer(serializers.Serializer):
    socket_key = serializers.UUIDField()


socket_key_schema = extend_schema(
    responses={
        200: SocketKeySerializer,
        401: OpenApiResponse(
            description="자격 인증 데이터가 제공되지 않았습니다.",
        ),
    },
    tags=["Socket Key"],
    summary="웹소켓 인증용 키 발급 api",
)
