from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import *
from core.models import *
from ..serializers import UserSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_full_name(request):
    first_name=request.data.get('first_name')
    last_name=request.data.get('last_name')
    if not first_name or not last_name:
        return Response({"error": "No Full Name"},status=HTTP_400_BAD_REQUEST)
    user = request.user
    user.first_name = first_name
    user.last_name = last_name
    user.save()
    return Response({"message": "Name updated successfully"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


