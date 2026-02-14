import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.throttling import ScopedRateThrottle

from giftsphere import settings
from ..models import Wishlist
from ..serializers import WishlistSerializer




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    wishlist = Wishlist.objects.filter(
        Q(user=request.user) | Q(shared=request.user)
    ).distinct()
    serializer = WishlistSerializer(wishlist, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_wishlist(request):
    wishlist_id=request.data.get('wishlist_id')

    if not wishlist_id:
        return Response(
            {"error": "wishlist_id is required"},
            status=HTTP_400_BAD_REQUEST
        )
    wishlist_item = Wishlist.objects.filter(
        user=request.user, id=wishlist_id
    )

    if not wishlist_item.exists():
        return Response(
            {"detail": "Wishlist item not found."},
            status=HTTP_404_NOT_FOUND
        )

    wishlist_item.delete()
    return Response(status=HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_wishlist(request):
    pass