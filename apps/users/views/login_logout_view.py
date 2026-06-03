from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception import ValidationException
from apps.users.serializers.login_logout_serializer import LoginSerializer
from apps.users.serializers.token_serializer import TokenResponseSerializer
from apps.users.services.login_logout_service import LoginService,LogoutService


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

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    service = LogoutService()
    def post(self,request:Request)->Response:
        refresh_token = request.COOKIES.get("refresh_token", "")

        self.service.logout(refresh_token)

        response = Response({
            "detail":"로그아웃 되었습니다."
        },status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response

