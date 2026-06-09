from django.urls import URLPattern, path

from apps.users.views import (
    check_nickname_view,
    email_view,
    login_logout_view,
    me_view,
    presigned_url_view,
    signup_view,
    token_view,
)

app_name = "users"

urlpatterns: list[URLPattern] = [
    path(
        "verification/send-email", email_view.EmailSendView.as_view(), name="send_email"
    ),
    path(
        "verification/verify-email",
        email_view.EmailVerifyView.as_view(),
        name="verify_email",
    ),
    path("signup", signup_view.SignupView.as_view(), name="signup"),
    path("login", login_logout_view.LoginView.as_view(), name="login"),
    path("logout", login_logout_view.LogoutView.as_view(), name="logout"),
    path("token/refresh", token_view.TokenView.as_view(), name="token_refresh"),
    path(
        "me/profile-image/presigned-url",
        presigned_url_view.UserProfileImgView.as_view(),
        name="presigned_url_image",
    ),
    path(
        "check-nickname",
        check_nickname_view.CheckNicknameView.as_view(),
        name="check_nickname",
    ),
    path("me", me_view.UserMeView.as_view(), name="me"),
]
