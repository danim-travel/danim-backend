"""

service에서 raise, view에서 BaseCustomException으로 catch 후 Response 반환
raise NotFoundException() → 기본 메시지
raise NotFoundException("커스텀 메시지") → 커스텀 메시지



# service
  def get_user(self, user_id: str) -> User:
      try:
          return User.objects.get(pk=user_id)
      except User.DoesNotExist:
          raise NotFoundException("해당 유저를 찾을 수 없습니다.")

  # view
  def get(self, request):
      try:
          user = self.service.get_user(request.user.id)
      except BaseCustomException as e: 또는 ----> except NotFoundException as e:
          return Response({"error_detail": e.message}, status=e.status_code)
      return Response(UserSerializer(user).data)
"""


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
