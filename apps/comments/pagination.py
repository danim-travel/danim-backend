from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommentPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100
    page_size = 10

    def get_page_number(self, request, _paginator):
        """
        query_parameter로 받을 page가 1보다 작거나 숫자로 형변환이 안되는 문자열이 들어왔을때
        모두 1로 반환하는 메서드
        """
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
            return page
        except (ValueError, TypeError):
            return 1

    def get_page_size(self, request):
        """
        query_parameter로 받을 page_size가 1보다 작거나 숫자로 형변환이 안되는 문자열이 들어왔을때
        또는 max_page_size보다 큰 page_size가 입력되었을때
        모두 class의 속성값 page_size(10)로 반환하는 메서드
        """
        try:
            page_size = int(request.query_params.get("page_size", 10))
            if page_size < 1:
                page_size = self.page_size
            elif page_size > self.max_page_size:
                page_size = self.max_page_size
            return page_size
        except (ValueError, TypeError):
            return self.page_size

    def get_paginated_response(self, data):
        """
        기존 pagination 클래스의 기본 응답에서 counts를 제거한 응답을 하는 메서드
        """
        return Response(
            {
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "results": data,
            }
        )
