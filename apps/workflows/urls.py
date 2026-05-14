from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UploadedAssetViewSet, WorkflowRunViewSet

router = DefaultRouter()
router.register("assets", UploadedAssetViewSet, basename="assets")
router.register("runs", WorkflowRunViewSet, basename="workflow-runs")

urlpatterns = [path("", include(router.urls))]
