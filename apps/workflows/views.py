from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import UploadedAsset, WorkflowRun
from .serializers import StartWorkflowSerializer, UploadedAssetSerializer, WorkflowRunSerializer
from .tasks import execute_workflow_run
from .utils import infer_asset_type


class UploadedAssetViewSet(viewsets.ModelViewSet):
    serializer_class = UploadedAssetSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UploadedAsset.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        uploaded = self.request.FILES.get("file")
        serializer.save(
            user=self.request.user,
            name=uploaded.name if uploaded else serializer.validated_data.get("name", "upload"),
            asset_type=infer_asset_type(uploaded.name if uploaded else ""),
        )


class WorkflowRunViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowRunSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return WorkflowRun.objects.filter(user=self.request.user).prefetch_related("logs", "assets").order_by("-created_at")

    @action(detail=False, methods=["post"])
    def start(self, request):
        serializer = StartWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workflow = WorkflowRun.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            query=serializer.validated_data.get("query", ""),
            state={"approval_required": serializer.validated_data["require_approval"]},
        )
        assets = UploadedAsset.objects.filter(user=request.user, id__in=serializer.validated_data.get("asset_ids", []))
        workflow.assets.set(assets)
        execute_workflow_run.delay(workflow.id)
        workflow.refresh_from_db()
        return Response(WorkflowRunSerializer(workflow).data, status=status.HTTP_202_ACCEPTED)
