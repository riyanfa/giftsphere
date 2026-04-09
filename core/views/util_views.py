from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import *
from ..models import Profile
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_contacts(request):
    contact_list = request.data.get('contacts', [])

    if not contact_list:
        return Response(
            {"error": "No contacts provided"},
            status=HTTP_400_BAD_REQUEST
        )

    # 2. Use __in to check if the phone_number exists in the provided list
    # Use .values_list to get only the numbers that exist
    existing_numbers = Profile.objects.filter(
        phone_number__in=contact_list
    ).values_list('phone_number', flat=True)

    # 3. Return the list of matches
    return Response({
        "existing_contacts": list(existing_numbers)
    }, status=HTTP_200_OK)