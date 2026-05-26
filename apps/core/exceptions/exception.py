from rest_framework.exceptions import APIException
from rest_framework import status

class BaseCustomException(APIException):
    status_code :int
    default_detail :str

class ValidationException(BaseCustomException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "잘못된 요청입니다."

class NotFoundException(BaseCustomException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "존재하지 않습니다."

class UnauthorizedException(BaseCustomException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "인증이 필요합니다."

class ConflictException(BaseCustomException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "이미 존재합니다."

class ForbiddenException(BaseCustomException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "접근 권한이 없습니다."

