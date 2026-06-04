from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.schemas import token_refresh_schema
from apps.users.serializers.token_serializer import (
    TokenRequestSerializer,
    TokenResponseSerializer,
)
from apps.users.services.token_service import TokenService


class TokenView(APIView):
    permission_classes = [AllowAny]
    service = TokenService()

    @token_refresh_schema
    def post(self, request: Request) -> Response:
        serializer = TokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh_token"]
        access_token = self.service.refresh_access_token(refresh_token)

        response = Response(
            TokenResponseSerializer({"access_token": access_token}).data,
            status=status.HTTP_200_OK,
        )
        response.set_cookie("refresh_token", refresh_token, httponly=True)
        return response
