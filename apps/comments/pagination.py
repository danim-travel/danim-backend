from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommentPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100
    page_size = 10

    def get_page_number(self, request, _paginator):
        try:
            page = int(request.query_params.get("page", 1))
            if page < 1:
                page = 1
            return page
        except (ValueError, TypeError):
            return 1

    def get_page_size(self, request):
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
        return Response(
            {
                "previous": self.get_previous_link(),
                "next": self.get_next_link(),
                "results": data,
            }
        )
