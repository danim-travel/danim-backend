class BaseCustomException(Exception):
    status_code: int
    default_message: str

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationException(BaseCustomException):
    status_code = 400
    default_message = "잘못된 요청입니다."


class NotFoundException(BaseCustomException):
    status_code = 404
    default_message = "존재하지 않습니다."


class UnauthorizedException(BaseCustomException):
    status_code = 401
    default_message = "인증이 필요합니다."


class ConflictException(BaseCustomException):
    status_code = 409
    default_message = "이미 존재합니다."


class ForbiddenException(BaseCustomException):
    status_code = 403
    default_message = "접근 권한이 없습니다."
