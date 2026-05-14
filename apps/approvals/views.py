from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.workflows.models import WorkflowRun

from .models import ApprovalRequest
from .serializers import ApprovalRequestSerializer


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return ApprovalRequest.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        approval = self.get_object()
        decision = request.data.get("status")
        if decision not in {ApprovalRequest.Status.APPROVED, ApprovalRequest.Status.REJECTED}:
            return Response({"detail": "status must be approved or rejected"}, status=400)
        approval.status = decision
        approval.decision_note = request.data.get("note", "")
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "decision_note", "decided_at"])
        approval.workflow.status = WorkflowRun.Status.COMPLETED if decision == ApprovalRequest.Status.APPROVED else WorkflowRun.Status.FAILED
        approval.workflow.save(update_fields=["status", "updated_at"])
        return Response(ApprovalRequestSerializer(approval).data)
