from django.urls import URLPattern, path

from apps.users.views import email_view, signup_view, token_view,login_logout_view


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
    path("me/refresh", token_view.TokenView.as_view(), name="token_refresh"),
]
