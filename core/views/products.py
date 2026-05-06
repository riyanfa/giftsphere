from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import AffiliateClick, GiftQuizAttempt, Product
from ..serializers import GiftQuizAttemptSerializer, ProductSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_product_collections(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .exclude(collection_name='')
        .select_related('category')
        .order_by('collection_name', 'id')
    )

    grouped = {}
    for product in products:
        grouped.setdefault(product.collection_name, []).append(product)

    collections = [
        {
            'name': name,
            'products': ProductSerializer(items, many=True).data,
        }
        for name, items in grouped.items()
    ]

    return Response({'collections': collections})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_featured_products(request):
    products = (
        Product.objects
        .filter(is_active=True, is_featured=True)
        .select_related('category')
        .order_by('id')
    )
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request):
    """
    List products with optional filtering.

    Query params:
      ?search=playstation   — case-insensitive match on name or description
      ?category=3           — filter by category ID
    """
    qs = Product.objects.filter(is_active=True).select_related('category').order_by('id')

    search = request.query_params.get('search', '').strip()
    category = request.query_params.get('category', '').strip()
    occasion = request.query_params.get('occasion', '').strip()
    target_gender = request.query_params.get('target_gender', '').strip()
    recipient_age = request.query_params.get('recipient_age', '').strip()
    budget_min = request.query_params.get('budget_min', '').strip()
    budget_max = request.query_params.get('budget_max', '').strip()
    interests = request.query_params.get('interests', '').strip()

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

    if category:
        try:
            qs = qs.filter(category_id=int(category))
        except ValueError:
            return Response({'error': 'category must be a valid integer ID.'}, status=400)

    if occasion:
        qs = qs.filter(occasion__iexact=occasion)

    if target_gender:
        qs = qs.filter(target_gender__iexact=target_gender)

    if recipient_age:
        try:
            age = int(recipient_age)
        except ValueError:
            return Response({'error': 'recipient_age must be a valid integer.'}, status=400)
        qs = qs.filter(Q(min_age__isnull=True) | Q(min_age__lte=age))
        qs = qs.filter(Q(max_age__isnull=True) | Q(max_age__gte=age))

    if budget_min:
        try:
            qs = qs.filter(price__gte=Decimal(budget_min))
        except InvalidOperation:
            return Response({'error': 'budget_min must be a valid number.'}, status=400)

    if budget_max:
        try:
            qs = qs.filter(price__lte=Decimal(budget_max))
        except InvalidOperation:
            return Response({'error': 'budget_max must be a valid number.'}, status=400)

    if interests:
        qs = qs.filter(interests__icontains=interests)

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_affiliate_click(request, product_id):
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)

    AffiliateClick.objects.create(user=request.user, product=product)
    return Response(
        {
            'message': 'Affiliate click recorded.',
            'affiliate_link': product.affiliate_link,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_quiz_attempt(request):
    required_fields = [
        'occasion',
        'recipient_age',
        'recipient_gender',
        'interests',
        'budget_min',
        'budget_max',
    ]
    missing = [field for field in required_fields if request.data.get(field) in [None, '']]
    if missing:
        return Response({'error': f"Missing required fields: {', '.join(missing)}"}, status=400)

    try:
        recipient_age = int(request.data.get('recipient_age'))
    except (TypeError, ValueError):
        return Response({'error': 'recipient_age must be a valid integer.'}, status=400)

    try:
        budget_min = Decimal(str(request.data.get('budget_min')))
        budget_max = Decimal(str(request.data.get('budget_max')))
    except InvalidOperation:
        return Response({'error': 'budget_min and budget_max must be valid numbers.'}, status=400)

    if budget_min < 0 or budget_max < 0 or budget_min > budget_max:
        return Response({'error': 'Budget range is invalid.'}, status=400)

    occasion = str(request.data.get('occasion')).strip()
    recipient_gender = str(request.data.get('recipient_gender')).strip()
    interests = str(request.data.get('interests')).strip()

    attempt = GiftQuizAttempt.objects.create(
        user=request.user,
        occasion=occasion,
        recipient_age=recipient_age,
        recipient_gender=recipient_gender,
        interests=interests,
        budget_min=budget_min,
        budget_max=budget_max,
    )

    products = (
        Product.objects
        .filter(is_active=True, price__gte=budget_min, price__lte=budget_max)
        .filter(Q(occasion='') | Q(occasion__iexact=occasion))
        .filter(Q(target_gender='') | Q(target_gender__iexact=recipient_gender))
        .filter(Q(min_age__isnull=True) | Q(min_age__lte=recipient_age))
        .filter(Q(max_age__isnull=True) | Q(max_age__gte=recipient_age))
        .filter(Q(interests='') | Q(interests__icontains=interests))
        .select_related('category')
        .order_by('price', 'id')[:10]
    )

    return Response(
        {
            'attempt': GiftQuizAttemptSerializer(attempt).data,
            'recommended_products': ProductSerializer(products, many=True).data,
        },
        status=201,
    )
