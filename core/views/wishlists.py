from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import *

from ..models import Wishlist, Product
from ..serializers import WishlistSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    wishlist = Wishlist.objects.filter(
        Q(user=request.user) | Q(shared=request.user)
    ).select_related('user').prefetch_related('products', 'shared').distinct()
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
    title=request.data.get('title','My Wishlist')
    title = title.strip()
    if not title:
        return Response({"error": "Title is required"}, status=HTTP_400_BAD_REQUEST)
    wishlist,created=Wishlist.objects.get_or_create(user=request.user,title=title)
    if not created:

        return Response(
            {"error": "You already have a wishlist with this title."},
            status=HTTP_409_CONFLICT)
    else:
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data, status=HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    product_id = request.data.get('product_id')
    wishlist_id = request.data.get('wishlist_id')

    if not wishlist_id or not product_id:
        return Response(
            {"error": "product_id or wishlist_id are missing"},
            status=HTTP_400_BAD_REQUEST
        )
    try:
        wishlist = Wishlist.objects.get(user=request.user, id=wishlist_id)
    except Wishlist.DoesNotExist:
        return Response(
            {"error": "Wishlist not found."},
            status=HTTP_404_NOT_FOUND
        )
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found."},
            status=HTTP_404_NOT_FOUND
        )
    if wishlist.products.filter(id=product.id).exists():
        return Response(
            {"message": "Product is already in the wishlist."},
            status=HTTP_409_CONFLICT
        )
    wishlist.products.add(product)
    return Response(
        {"message": "Product successfully added."},
        status=HTTP_201_CREATED
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request):
    product_id = request.data.get('product_id')
    wishlist_id = request.data.get('wishlist_id')

    if not wishlist_id or not product_id:
        return Response(
            {"error": "product_id and wishlist_id are required"},
            status=HTTP_400_BAD_REQUEST
        )
    try:
        wishlist = Wishlist.objects.get(user=request.user, id=wishlist_id)
    except Wishlist.DoesNotExist:
        return Response(
            {"error": "Wishlist not found."},
            status=HTTP_404_NOT_FOUND
        )
    if not wishlist.products.filter(id=product_id).exists():
        return Response(
            {"error": "Product not in wishlist."},
            status=HTTP_404_NOT_FOUND
        )
    wishlist.products.remove(product_id)
    return Response(
        {"message": "Product removed from wishlist."},
        status=HTTP_200_OK
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_wishlist_title(request):
    wishlist_id = request.data.get('wishlist_id')
    new_title = request.data.get('title', '').strip()

    if not wishlist_id:
        return Response(
            {"error": "wishlist_id is required"},
            status=HTTP_400_BAD_REQUEST
        )
    if not new_title:
        return Response(
            {"error": "title is required"},
            status=HTTP_400_BAD_REQUEST
        )
    try:
        wishlist = Wishlist.objects.get(user=request.user, id=wishlist_id)
    except Wishlist.DoesNotExist:
        return Response(
            {"error": "Wishlist not found."},
            status=HTTP_404_NOT_FOUND
        )
    # Check if another wishlist with same title exists
    if Wishlist.objects.filter(user=request.user, title=new_title).exclude(id=wishlist_id).exists():
        return Response(
            {"error": "You already have a wishlist with this title."},
            status=HTTP_409_CONFLICT
        )
    wishlist.title = new_title
    wishlist.save()
    serializer = WishlistSerializer(wishlist)
    return Response(serializer.data, status=HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_wishlist_visibility(request):
    wishlist_id = request.data.get('wishlist_id')
    visibility = request.data.get('visibility', '').upper()

    if not wishlist_id:
        return Response(
            {"error": "wishlist_id is required"},
            status=HTTP_400_BAD_REQUEST
        )
    valid_choices = [choice[0] for choice in Wishlist.VISIBILITY_CHOICES]
    if visibility not in valid_choices:
        return Response(
            {"error": f"visibility must be one of: {valid_choices}"},
            status=HTTP_400_BAD_REQUEST
        )
    try:
        wishlist = Wishlist.objects.get(user=request.user, id=wishlist_id)
    except Wishlist.DoesNotExist:
        return Response(
            {"error": "Wishlist not found."},
            status=HTTP_404_NOT_FOUND
        )
    wishlist.visibility = visibility
    wishlist.save()
    serializer = WishlistSerializer(wishlist)
    return Response(serializer.data, status=HTTP_200_OK)