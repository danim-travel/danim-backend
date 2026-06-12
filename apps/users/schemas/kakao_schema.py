from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from apps.users.serializers.kakao_serializer import KakaoSignupSerializer

kakao_login_schema = extend_schema(
    tags=["social-login"],
    summary="카카오 로그인 시작",
    description="카카오 OAuth 인가 페이지로 리다이렉트합니다. (브라우저에서 직접 접근)",
    responses={
        302: OpenApiResponse(description="카카오 인가 페이지로 리다이렉트"),
    },
)

kakao_callback_schema = extend_schema(
    tags=["social-login"],
    summary="카카오 로그인 콜백",
    description=(
        "카카오가 전달한 code/state를 검증·처리합니다.\n"
        "- 기존 유저: refresh_token 쿠키 설정 후 로그인 성공 페이지로 리다이렉트\n"
        "- 신규 유저: signup_token과 함께 회원가입 페이지로 리다이렉트"
    ),
    parameters=[
        OpenApiParameter(
            name="code",
            type=str,
            location=OpenApiParameter.QUERY,
            description="카카오 인가 코드",
        ),
        OpenApiParameter(
            name="state",
            type=str,
            location=OpenApiParameter.QUERY,
            description="CSRF 방지용 state 값",
        ),
    ],
    responses={
        302: OpenApiResponse(
            description="로그인 성공(기존 유저) 또는 회원가입 페이지(신규 유저)로 리다이렉트"
        ),
        400: OpenApiResponse(
            description="유효하지 않은 요청(state 불일치) 또는 카카오 인증 실패"
        ),
    },
)

kakao_signup_schema = extend_schema(
    tags=["social-login"],
    summary="카카오 회원가입 완료 (2단계)",
    description=(
        "콜백에서 받은 signup_token과 추가 정보(nickname, name, birth_day)로 "
        "회원가입을 완료합니다. "
        "성공 시 access_token(body)과 refresh_token(httpOnly 쿠키)을 발급합니다."
    ),
    request=KakaoSignupSerializer,
    responses={
        201: inline_serializer(
            name="KakaoSignupResponse",
            fields={"access_token": serializers.CharField()},
        ),
        400: OpenApiResponse(
            description="입력값 검증 실패(닉네임 형식 등) 또는 가입 시간 만료"
        ),
        409: OpenApiResponse(description="이미 존재하는 이메일 또는 닉네임입니다."),
    },
)
