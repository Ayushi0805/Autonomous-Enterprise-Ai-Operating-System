from django.conf import settings
from django.db import models


class MemoryRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    namespace = models.CharField(max_length=100, default="general")
    key = models.CharField(max_length=255)
    value = models.JSONField(default=dict)
    importance = models.FloatField(default=0.5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "namespace", "key")
        ordering = ["-updated_at"]
