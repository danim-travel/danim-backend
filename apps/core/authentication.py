from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationNoWWW(JWTAuthentication):
    def authenticate_header(self, request):
        return None
