from django.urls import URLPattern, path

from apps.users.views import (
    change_password_view,
    check_nickname_view,
    email_view,
    follow_view,
    google_view,
    kakao_view,
    login_logout_view,
    me_view,
    presigned_url_view,
    profile_view,
    reset_password_view,
    signup_view,
    token_view,
    user_search_view,
)

app_name = "users"

urlpatterns: list[URLPattern] = [
    path(
        "/verification/send-email", email_view.EmailSendView.as_view(), name="send_email"
    ),
    path(
        "/verification/verify-email",
        email_view.EmailVerifyView.as_view(),
        name="verify_email",
    ),
    path("/signup", signup_view.SignupView.as_view(), name="signup"),
    path("/login", login_logout_view.LoginView.as_view(), name="login"),
    path("/logout", login_logout_view.LogoutView.as_view(), name="logout"),
    path("/token/refresh", token_view.TokenView.as_view(), name="token_refresh"),
    path(
        "/me/profile-image/presigned-url",
        presigned_url_view.UserProfileImgView.as_view(),
        name="presigned_url_image",
    ),
    path(
        "/check-nickname",
        check_nickname_view.CheckNicknameView.as_view(),
        name="check_nickname",
    ),
    path("/me", me_view.UserMeView.as_view(), name="me"),
    path("", user_search_view.UserSearchView.as_view(), name="user_search"),
    path(
        "/social-login/kakao/login",
        kakao_view.KakaoLoginView.as_view(),
        name="kakao_login",
    ),
    path(
        "/social-login/kakao/callback",
        kakao_view.KakaoCallbackView.as_view(),
        name="kakao_callback",
    ),
    path("/<str:user_id>/followers", follow_view.Followers.as_view(), name="followers"),
    path(
        "/change-password",
        change_password_view.ChangePasswordView.as_view(),
        name="change_password",
    ),
    path("/<str:user_id>/following", follow_view.Following.as_view(), name="following"),
    path("/<str:user_id>/profile", profile_view.ProfileView.as_view(), name="profile"),
    path(
        "/reset-password",
        reset_password_view.ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "/social-login/google/login",
        google_view.GoogleLoginView.as_view(),
        name="google_login",
    ),
    path(
        "/social-login/google/callback",
        google_view.GoogleCallbackView.as_view(),
        name="google_callback",
    ),
]
