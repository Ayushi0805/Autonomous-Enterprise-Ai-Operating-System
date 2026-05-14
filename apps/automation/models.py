from django.conf import settings
from django.db import models


class AutomationRun(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    workflow = models.ForeignKey("workflows.WorkflowRun", on_delete=models.CASCADE, null=True, blank=True)
    channel = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=30, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
