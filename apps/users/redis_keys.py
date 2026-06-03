class EmailRedisKey:
    @staticmethod
    def code(purpose: str, email: str) -> str:
        return f"email:code:{purpose}:{email}"

    @staticmethod
    def token(purpose: str, token: str) -> str:
        return f"email:token:{purpose}:{token}"

class LoginRedisKey:
    @staticmethod
    def blacklist(jti:str) -> str:
        return f"blacklist:refresh_token:{jti}"