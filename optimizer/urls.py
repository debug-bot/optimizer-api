from .views import OptimizerFileViewSet, TableViewSet, FieldsViewSet
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register("table", TableViewSet, basename="table")
router.register("fields", FieldsViewSet, basename="fields")

urlpatterns = [
    path("", include(router.urls)),
    path("optimizer-file/", OptimizerFileViewSet.as_view(), name="optimizer-file"),
]
