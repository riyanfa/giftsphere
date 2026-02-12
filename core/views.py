import random

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.status import HTTP_400_BAD_REQUEST

from .models import *
from .serializers import ProductSerializer



@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    phone = request.data.get('phone')
    if not phone:
        return Response({"error": "Phone number is required"}, status=HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(username=phone)

    profile, _ = Profile.objects.get_or_create(user=user, defaults={'phone_number': phone})

    otp = str(random.randint(1000, 9999))
    profile.otp_code = otp
    profile.save()

    print(f"\n==================================")
    print(f" OTP FOR {phone} IS: {otp}")
    print(f"==================================\n")

    return Response({"message": "OTP Sent Successfully"})


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    phone = request.data.get('phone')
    code = request.data.get('otp')
    try:
        user = User.objects.get(username=phone)
        profile = Profile.objects.get(user=user)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=400)
    # debug!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if profile.otp_code == code or code == "1234": # 1234 is for debugging currently
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.id})
    else:
        return Response({"error": "Invalid OTP"}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    pass
