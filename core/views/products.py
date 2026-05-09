from decimal import Decimal, InvalidOperation

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
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
      ?search=playstation   - full-text search on product browsing fields
      ?category=3           - filter by category ID
      ?category=Electronics - filter by category name
      ?budget_min=100       - minimum product price
      ?budget_max=400       - maximum product price
    """
    qs = Product.objects.filter(is_active=True).select_related('category')

    search = request.query_params.get('search', '').strip()
    category = request.query_params.get('category', '').strip()
    budget_min = request.query_params.get('budget_min', '').strip()
    budget_max = request.query_params.get('budget_max', '').strip()

    if search:
        search_vector = (
            SearchVector('name', weight='A')
            + SearchVector('category__name', weight='A')
            + SearchVector('interests', weight='B')
            + SearchVector('occasion', weight='B')
            + SearchVector('description', weight='C')
            + SearchVector('store_name', weight='D')
        )
        search_query = SearchQuery(search, search_type='websearch')
        qs = (
            qs
            .annotate(search_vector=search_vector, rank=SearchRank(search_vector, search_query))
            .filter(search_vector=search_query)
        )

    if category:
        if category.isdecimal():
            qs = qs.filter(category_id=int(category))
        else:
            qs = qs.filter(category__name__iexact=category)

    if budget_min:
        try:
            min_price = Decimal(budget_min)
        except InvalidOperation:
            return Response({'error': 'budget_min must be a valid number.'}, status=400)
        if not min_price.is_finite():
            return Response({'error': 'budget_min must be a valid number.'}, status=400)
        qs = qs.filter(price__gte=min_price)

    if budget_max:
        try:
            max_price = Decimal(budget_max)
        except InvalidOperation:
            return Response({'error': 'budget_max must be a valid number.'}, status=400)
        if not max_price.is_finite():
            return Response({'error': 'budget_max must be a valid number.'}, status=400)
        qs = qs.filter(price__lte=max_price)

    if search:
        qs = qs.order_by('-rank', 'id')
    else:
        qs = qs.order_by('id')

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
