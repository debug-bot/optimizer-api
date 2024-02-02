from numpy import number
from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size_query_param = "limit"
    page_size = 10
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.__len__(),
                "currentPage": self.page.number,
                "hasMorePages": self.page.has_other_pages(),
                "lastPage": self.page.paginator.page_range[-1],
                "perPage": self.get_page_size(self.request),
                "total": self.page.paginator.count,
                "data": data,
            }
        )
