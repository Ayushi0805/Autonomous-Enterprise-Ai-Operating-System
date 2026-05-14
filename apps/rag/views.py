from rest_framework import permissions, serializers, views
from rest_framework.response import Response

from apps.workflows.models import UploadedAsset

from .services import RAGService


class SemanticSearchSerializer(serializers.Serializer):
    query = serializers.CharField()
    asset_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class DocumentIngestSerializer(serializers.Serializer):
    asset_ids = serializers.ListField(child=serializers.IntegerField())


class DocumentIngestView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = DocumentIngestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assets = UploadedAsset.objects.filter(user=request.user, id__in=serializer.validated_data["asset_ids"])
        docs = [{"id": a.id, "name": a.name, "path": a.file.path, "asset_type": a.asset_type} for a in assets]
        return Response(RAGService().ingest(docs))


class SemanticSearchView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = SemanticSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assets = UploadedAsset.objects.filter(user=request.user, id__in=serializer.validated_data.get("asset_ids", []))
        docs = [{"id": a.id, "name": a.name, "path": a.file.path, "asset_type": a.asset_type} for a in assets]
        return Response({"results": RAGService().retrieve(serializer.validated_data["query"], docs)})
