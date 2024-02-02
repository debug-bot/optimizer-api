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
    openapi.Parameter(
        "search",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        description="Search query",
    ),
    openapi.Parameter(
        "ordering",
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
        description="Ordering field",
    ),
]
