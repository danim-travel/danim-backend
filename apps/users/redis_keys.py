class EmailRedisKey:
    @staticmethod
    def code(purpose: str, email: str) -> str:
        return f"email:code:{purpose}:{email}"

    @staticmethod
    def token(purpose: str, token: str) -> str:
        return f"email:token:{purpose}:{token}"

    @staticmethod
    def cooldown(purpose: str, email: str) -> str:  # 추가
        return f"email:cooldown:{purpose}:{email}"

    @staticmethod
    def verify_fail(purpose: str, email: str) -> str:
        return f"email:verify_fail:{purpose}:{email}"


class LoginRedisKey:
    @staticmethod
    def blacklist(jti: str) -> str:
        return f"blacklist:refresh_token:{jti}"


class SocialRedisKey:
    @staticmethod
    def state(state: str) -> str:
        return f"social:state:{state}"

    @staticmethod
    def signup(token: str) -> str:
        return f"social:signup:{token}"
