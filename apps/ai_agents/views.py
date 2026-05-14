from rest_framework import permissions, viewsets

from .models import AgentDefinition
from .serializers import AgentDefinitionSerializer


class AgentDefinitionViewSet(viewsets.ModelViewSet):
    queryset = AgentDefinition.objects.all().order_by("name")
    serializer_class = AgentDefinitionSerializer
    permission_classes = (permissions.IsAuthenticated,)
