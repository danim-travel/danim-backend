from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.signup_serializer import UserSignUpSerializer

signup_schema = extend_schema(
    tags=["users"],
    summary="회원가입",
    description="이메일 인증(email_token)과 유저 정보를 받아 회원가입을 진행합니다.",
    request=UserSignUpSerializer,
    responses={
        201: inline_serializer(
            name="SignupResponse",
            fields={
                "detail": serializers.CharField(default="회원가입이 완료되었습니다.")
            },
        ),
        400: OpenApiResponse(
            description="입력값 검증 실패 (비밀번호 규칙, 닉네임 형식, 비밀번호 불일치 등)"
        ),
        404: OpenApiResponse(
            description="유효하지 않은 이메일입니다. (email_token 만료/위조)"
        ),
        409: OpenApiResponse(description="이미 존재하는 이메일 또는 닉네임입니다."),
        500: OpenApiResponse(description="서버 오류로 회원가입에 실패했습니다."),
    },
)
