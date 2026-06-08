from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationNoWWW(JWTAuthentication):
    def authenticate_header(self, request):
        return ""


class JWTAuthenticationNoWWWScheme(OpenApiAuthenticationExtension):
    target_class = "apps.core.authentication.JWTAuthenticationNoWWW"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
