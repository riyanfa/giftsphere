from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from ..models import *
from ..serializers import ProductSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request):
    paginator = LimitOffsetPagination()
    paginator.default_limit = 10
    products = Product.objects.all()
    paginated_products = paginator.paginate_queryset(products, request)
    serializer = ProductSerializer(paginated_products, many=True)
    return paginator.get_paginated_response(serializer.data)
