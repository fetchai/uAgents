from rest_framework import serializers

class GeminSerializer(serializers.Serializer):
    prompt = serializers.CharField()