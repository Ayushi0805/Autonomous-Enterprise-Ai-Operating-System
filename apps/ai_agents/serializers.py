from rest_framework import serializers

from .models import AgentDefinition


class AgentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDefinition
        fields = "__all__"
