from rest_framework import serializers

from .models import AgentExecutionLog, UploadedAsset, WorkflowRun


class UploadedAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedAsset
        fields = "__all__"
        read_only_fields = ("user", "asset_type", "metadata")


class AgentExecutionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecutionLog
        fields = "__all__"


class WorkflowRunSerializer(serializers.ModelSerializer):
    logs = AgentExecutionLogSerializer(many=True, read_only=True)

    class Meta:
        model = WorkflowRun
        fields = "__all__"
        read_only_fields = ("user", "status", "state", "workflow_type", "final_response")


class StartWorkflowSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    query = serializers.CharField(allow_blank=True, required=False)
    asset_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    require_approval = serializers.BooleanField(default=False)
