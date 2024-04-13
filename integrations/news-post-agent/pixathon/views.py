
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .serializers import *
from .services import *


@api_view(["POST"])
def desc(request):
    serializer = GeminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    prompt = serializer.validated_data["prompt"]
    result = geminiOP(prompt)
    return Response({"result": result}, status=status.HTTP_200_OK)

@api_view(["POST"])
def prompts(request):
    serializer = GeminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    prompt = serializer.validated_data["prompt"]
    result = geminiPrompts(prompt)
    return Response({"result": result}, status=status.HTTP_200_OK)

    