from django.urls import URLPattern, path
from apps.users.views import email_view,signup_view

app_name = "users"

urlpatterns: list[URLPattern] = [
    path("verification/send-email",email_view.EmailSendView.as_view(),name="send_email"),
    path("verification/verify-email",email_view.EmailVerifyView.as_view(),name="verify_email"),
    path("signup",signup_view.SignupView.as_view(),name="signup"),

]
