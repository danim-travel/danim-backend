from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is not None:
        if "detail" in response.data:
            response.data = {
                "error_detail": str(response.data["detail"]),
                "status_code": response.status_code,
            }
        else:
            response.data = {
                "error_detail": response.data,
                "status_code": response.status_code,
            }
    return response