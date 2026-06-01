from rest_framework import status
from rest_framework.exceptions import APIException

"""
  DRF 기본 예외 응답 형태를 error_detail + status_code로 통일하는 핸들러
  settings.py의 EXCEPTION_HANDLER에 등록되어 자동으로 호출됨

  [ APIException 계열 예외 ]
  service에서 raise하면 view에서 try/except 없이 자동으로 처리됨

      # service
      def get_user(self, user_id: str) -> User:
          try:
              return User.objects.get(pk=user_id)
          except User.DoesNotExist:
              raise NotFoundException()                  # 기본 메시지
              raise NotFoundException("커스텀 메시지")    # 커스텀 메시지

      # 응답
      {"error_detail": "존재하지 않습니다.", "status_code": 404}
      {"error_detail": "커스텀 메시지", "status_code": 404}

  [ ValidationError ]
  serializer.is_valid(raise_exception=True) 호출 시 자동으로 처리됨

      # view
      serializer.is_valid(raise_exception=True)

      # 응답
      {"error_detail": {"email": ["이 필드는 필수입니다."]}, "status_code": 400}
  """


class BaseCustomException(APIException):
    status_code: int
    default_detail: str


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
