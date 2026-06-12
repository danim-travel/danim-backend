from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.schemas.kakao_schema import (
    kakao_callback_schema,
    kakao_login_schema,
    kakao_signup_schema,
)
from apps.users.serializers.kakao_serializer import KakaoSignupSerializer
from apps.users.services.kakao_service import KakaoService


class KakaoCallbackView(APIView):
    permission_classes = [AllowAny]
    service = KakaoService()

    @kakao_callback_schema
    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.GET.get("code", "")
        state = request.GET.get("state", "")
        result = self.service.kakao_callback(code, state)
        if result["is_new"]:
            return redirect(
                f"{settings.FRONT_REDIRECT_URI}/signup?signup_token={result['signup_token']}"
            )
        response = redirect(f"{settings.FRONT_REDIRECT_URI}/login/success")
        response.set_cookie(
            "refresh_token",
            result["refresh_token"],
            httponly=True,
            samesite="None",
            secure=True,
        )
        return response


class KakaoSignupView(APIView):
    permission_classes = [AllowAny]
    service = KakaoService()

    @kakao_signup_schema
    def post(self, request: Request) -> Response:
        serializer = KakaoSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access, refresh = self.service.complete_signup(**serializer.validated_data)

        response = Response({"access_token": access}, status=status.HTTP_201_CREATED)
        response.set_cookie(
            "refresh_token",
            refresh,
            httponly=True,
            samesite="None",
            secure=True,
        )
        return response


class KakaoLoginView(APIView):
    permission_classes = [AllowAny]
    service = KakaoService()

    @kakao_login_schema
    def get(self, request: Request) -> HttpResponseRedirect:
        url = self.service.build_authorize_url()
        return redirect(url)
