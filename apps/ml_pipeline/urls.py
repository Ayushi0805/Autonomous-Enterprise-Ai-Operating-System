from django.urls import path

from .views import TrainLoRAView, TrainModelView

urlpatterns = [
    path("train/", TrainModelView.as_view(), name="train-model"),
    path("lora/train/", TrainLoRAView.as_view(), name="train-lora"),
]
