from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.login_logout_serializer import LoginSerializer
from apps.users.serializers.token_serializer import TokenResponseSerializer
from apps.users.services.login_logout_service import LoginService


class LoginView(APIView):
    permission_classes = [AllowAny]
    service = LoginService()

    def post(self, request: Request) -> Response:
        """
        POST api/v1/users/login
        로그인 api
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        old_refresh_token = request.COOKIES.get("refresh_token", "")

        access_token, refresh_token = self.service.login(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
            old_refresh_token=old_refresh_token,
        )
        response = Response(
            TokenResponseSerializer({"access_token": access_token}).data,
            status=status.HTTP_200_OK,
        )
        response.set_cookie("refresh_token", refresh_token, httponly=True)

        return response
