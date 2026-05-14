from rest_framework import permissions, viewsets

from .models import MemoryRecord
from .serializers import MemoryRecordSerializer


class MemoryRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MemoryRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return MemoryRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
