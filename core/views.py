import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.throttling import ScopedRateThrottle

from giftsphere import settings
from .models import *
from .serializers import ProductSerializer, WishlistSerializer, UserMeSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def request_otp(request):
    phone = request.data.get('phone')

    if not phone:
        return Response({"error": "Phone number is required"}, status=HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(username=phone)

    profile, _ = Profile.objects.get_or_create(user=user, defaults={'phone_number': phone})

    otp = str(secrets.randbelow(9000) + 1000)
    profile.otp_code = make_password(otp)
    profile.otp_created_at = timezone.now()
    profile.save()
    response_data = {"message": "OTP Sent Successfully"}

    if settings.DEBUG:
        response_data["debug_otp"] = otp

    return Response(response_data)


request_otp.throttle_scope = 'otp_request'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def verify_otp(request):
    phone = request.data.get('phone')
    code = request.data.get('otp')
    if not phone or not code:
        return Response({"error": "Phone and OTP required"}, status=400)

    try:
        user = User.objects.get(username=phone)
        profile = Profile.objects.get(user=user)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=400)

    if not profile.otp_code:
        return Response({"error": "No OTP requested"}, status=400)

    if timezone.now() - profile.otp_created_at > timedelta(minutes=5):
        return Response({"error": "OTP expired"}, status=400)
    if profile.otp_attempts >= 3:
        return Response({"error": "Too many attempts. Request new OTP."}, status=400)
    if check_password(code, profile.otp_code):
        profile.otp_code = None
        profile.otp_attempts = 0
        profile.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response(
            {
                "token": token.key,
            })
    else:
        profile.otp_attempts += 1
        profile.save()
        return Response({"error": "Invalid OTP"}, status=400)


verify_otp.throttle_scope = 'otp_verify'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    wishlist = Wishlist.objects.get(user=request.user or Wishlist.user.shared_wishlists.contains(request.user))
    serializer = WishlistSerializer(wishlist, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    serializer = UserMeSerializer(request.user)
    return Response(serializer.data)
