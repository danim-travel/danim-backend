from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.signup_serializer import UserSignUpSerializer
from apps.users.services.signup_service import SignUpService


class SignupView(APIView):
    """
    POST api/v1/users/signup
    유저 회원가입에 관한 class
    """

    permission_classes = [AllowAny]
    service = SignUpService()

    def post(self, request: Request) -> Response:
        """
        user로 부터 data를 받아 유저를 생성하는 view
        """
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.create_user(serializer.validated_data)
        return Response(
            {
                "detail": "회원가입이 완료되었습니다.",
            },
            status=status.HTTP_201_CREATED,
        )
