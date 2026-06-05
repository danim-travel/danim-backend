from django.db.models import QuerySet
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

"""
view에서 

from apps.core.utils.pagination import paginate

임포트 해서 사용하기

def get(self,request):
    queryset = service.get_list(...) #  service가 조회할 쿼리셋을 만들어 반환 (lazy)
    return paginate(queryset,request,SomeSerializer) # 기본 10개 단위 커서 페이지네이션


"""


class DefaultPagination(CursorPagination):
    page_size = 10
    ordering = "-id"
    page_size_query_param = "page_size"
    max_page_size = 100


def paginate(
    queryset: QuerySet,
    request: Request,
    serializer_class: type[BaseSerializer],
    pagination_class: type[CursorPagination] = DefaultPagination,
) -> Response:
    """쿼리셋을 커서 페이지네이션해서 Response까지 반환.

    사용법 (목록 조회 view):
        def get(self, request):
            queryset = service.get_list(...)   # service가 쿼리셋 반환 (lazy)
            return paginate(queryset, request, SomeSerializer)

    - 응답: {previous, next, results} (기본 10개, ?page_size=N 으로 조절, 최대 100)
    - ?cursor= 로 다음 페이지 (무한스크롤은 응답의 next URL을 따라가면 됨)
    """
    paginator = pagination_class()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context={"request": request})
    return paginator.get_paginated_response(serializer.data)
