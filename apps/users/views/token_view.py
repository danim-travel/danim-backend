from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.schemas import token_refresh_schema
from apps.users.serializers.token_serializer import TokenResponseSerializer
from apps.users.services.token_service import TokenService


class TokenView(APIView):
    permission_classes = [AllowAny]
    service = TokenService()

    @token_refresh_schema
    def post(self, request: Request) -> Response:
        # refresh_token은 httpOnly 쿠키로 내려가므로 body가 아닌 쿠키에서 읽는다.
        # (로그아웃 엔드포인트와 동일한 방식)
        refresh_token = request.COOKIES.get("refresh_token", "")
        access_token = self.service.refresh_access_token(refresh_token)

        return Response(
            TokenResponseSerializer({"access_token": access_token}).data,
            status=status.HTTP_200_OK,
        )
