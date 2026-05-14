from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgentDefinitionViewSet

router = DefaultRouter()
router.register("", AgentDefinitionViewSet, basename="agents")
urlpatterns = [path("", include(router.urls))]
