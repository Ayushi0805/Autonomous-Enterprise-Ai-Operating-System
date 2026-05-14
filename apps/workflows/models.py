from django.conf import settings
from django.db import models


class UploadedAsset(models.Model):
    class AssetType(models.TextChoices):
        PDF = "pdf", "PDF"
        CSV = "csv", "CSV"
        EXCEL = "excel", "Excel"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        TEXT = "text", "Text"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    asset_type = models.CharField(max_length=20, choices=AssetType.choices, default=AssetType.OTHER)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkflowRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        WAITING_APPROVAL = "waiting_approval", "Waiting Approval"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    query = models.TextField(blank=True)
    workflow_type = models.CharField(max_length=100, blank=True)
    assets = models.ManyToManyField(UploadedAsset, blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    state = models.JSONField(default=dict, blank=True)
    final_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class AgentExecutionLog(models.Model):
    workflow = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name="logs")
    agent_name = models.CharField(max_length=100)
    input_snapshot = models.JSONField(default=dict, blank=True)
    output = models.JSONField(default=dict, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
