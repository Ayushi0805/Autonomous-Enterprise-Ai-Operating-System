from django.urls import path

from .views import TriggerAutomationView

urlpatterns = [path("trigger/", TriggerAutomationView.as_view(), name="trigger-automation")]
