from rest_framework import permissions, serializers, views
from rest_framework.response import Response

from .models import AutomationRun
from .tasks import trigger_automation


class AutomationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationRun
        fields = "__all__"
        read_only_fields = ("user", "status")


class TriggerAutomationView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        data = request.data.copy()
        # Handle cases where n8n sends IDs as strings
        if "workflow" in data and isinstance(data["workflow"], str):
            try:
                # Remove any stray '=' or quotes if n8n accidentally sends them
                clean_id = data["workflow"].strip("=\"' ")
                data["workflow"] = int(clean_id)
            except (ValueError, TypeError):
                pass

        serializer = AutomationSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        run = serializer.save(user=request.user)
        trigger_automation.delay(run.id)
        return Response(AutomationSerializer(run).data, status=202)
