from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.exceptions.exception import ConflictException
from apps.users.models import LoginType
from apps.users.schemas.google_schema import (
    google_callback_schema,
    google_login_schema,
)
from apps.users.services.google_service import GoogleService


class GoogleCallbackView(APIView):
    permission_classes = [AllowAny]
    service = GoogleService()

    @google_callback_schema
    def get(self, request: Request) -> HttpResponseRedirect:
        code = request.GET.get("code", "")
        state = request.GET.get("state", "")
        try:
            result = self.service.google_callback(code, state)
        except ConflictException:
            return redirect(
                f"{settings.FRONT_REDIRECT_URI}?provider={LoginType.GOOGLE}&is_success=false&reason=email_exists"
            )
        response = redirect(
            f"{settings.FRONT_REDIRECT_URI}?provider={LoginType.GOOGLE}&is_success=true"
        )
        response.set_cookie(
            "refresh_token",
            result["refresh_token"],
            httponly=True,
            samesite="None",
            secure=True,
        )
        return response


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    service = GoogleService()

    @google_login_schema
    def get(self, request: Request) -> HttpResponseRedirect:
        url = self.service.build_authorize_url()
        return redirect(url)
