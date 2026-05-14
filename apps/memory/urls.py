from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MemoryRecordViewSet

router = DefaultRouter()
router.register("", MemoryRecordViewSet, basename="memory")
urlpatterns = [path("", include(router.urls))]
