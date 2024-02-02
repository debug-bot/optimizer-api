from .views import DeviceViewSet, OptimizerFileViewSet, TableViewSet
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register("device", DeviceViewSet, basename="device")
router.register("table", TableViewSet, basename="table")

urlpatterns = [
    path("", include(router.urls)),
    path("optimizer-file/", OptimizerFileViewSet.as_view(), name="optimizer-file"),
]
