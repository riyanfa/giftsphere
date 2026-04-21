from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Product
from ..serializers import ProductSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request):
    """
    List products with optional filtering.

    Query params:
      ?search=playstation   — case-insensitive match on name or description
      ?category=3           — filter by category ID
    """
    qs = Product.objects.select_related('category').order_by('id')

    search = request.query_params.get('search', '').strip()
    category = request.query_params.get('category', '').strip()

    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(description__icontains=search)

    if category:
        try:
            qs = qs.filter(category_id=int(category))
        except ValueError:
            return Response({'error': 'category must be a valid integer ID.'}, status=400)

    paginator = LimitOffsetPagination()
    paginator.default_limit = 10
    paginated = paginator.paginate_queryset(qs, request)
    serializer = ProductSerializer(paginated, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_product_detail(request, product_id):
    """
    Fetch a single product by ID.
    Used by the Flutter catalog → Qattah creation flow.
    """
    try:
        product = Product.objects.select_related('category').get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)

    serializer = ProductSerializer(product)
    return Response(serializer.data)
