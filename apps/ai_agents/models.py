from django.db import models


class AgentDefinition(models.Model):
    name = models.CharField(max_length=100, unique=True)
    responsibility = models.TextField()
    tools = models.JSONField(default=list, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
