from rest_framework import permissions, views
from rest_framework.response import Response

from apps.workflows.models import UploadedAsset

from .services import EDAService


class EDAView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        assets = UploadedAsset.objects.filter(user=request.user, id__in=request.data.get("asset_ids", []))
        docs = [{"id": a.id, "name": a.name, "path": a.file.path, "asset_type": a.asset_type} for a in assets]
        return Response(EDAService().run(docs))
