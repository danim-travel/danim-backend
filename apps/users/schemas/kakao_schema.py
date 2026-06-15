from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

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
        "- 기존 유저: 로그인 처리\n"
        "- 신규 유저: 자동 가입(기본값) 후 로그인 처리\n"
        "공통적으로 refresh_token 쿠키 설정 후 로그인 성공 페이지로 리다이렉트합니다."
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
        302: OpenApiResponse(description="로그인 성공 페이지로 리다이렉트"),
        400: OpenApiResponse(
            description="유효하지 않은 요청(state 불일치) 또는 카카오 인증 실패"
        ),
    },
)
