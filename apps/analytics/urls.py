from django.urls import path

from .views import EDAView

urlpatterns = [path("eda/", EDAView.as_view(), name="eda")]
