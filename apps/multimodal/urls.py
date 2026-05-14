from django.urls import path

from .views import VisionAnalyzeView

urlpatterns = [path("vision/analyze/", VisionAnalyzeView.as_view(), name="vision-analyze")]
