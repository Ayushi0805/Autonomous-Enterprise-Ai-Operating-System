from rest_framework import serializers

from .models import MemoryRecord


class MemoryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemoryRecord
        fields = "__all__"
        read_only_fields = ("user",)
