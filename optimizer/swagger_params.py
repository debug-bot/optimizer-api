from drf_yasg import openapi

table_params = [
    openapi.Parameter(
        "page",
        openapi.IN_QUERY,
        type=openapi.TYPE_NUMBER,
        description="Page number",
    ),
    openapi.Parameter(
        "per_page",
        openapi.IN_QUERY,
        type=openapi.TYPE_NUMBER,
        description="Number of records per page",
    ),
]
