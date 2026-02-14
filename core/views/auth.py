import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import *
from rest_framework.throttling import ScopedRateThrottle

from giftsphere import settings
from ..models import *


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([ScopedRateThrottle])
def request_otp(request):
    phone = request.data.get('phone')
    if not (phone.startswith('5') and len(phone) == 9):
        return Response({"error":"Wrong phone number"},status=HTTP_400_BAD_REQUEST)
    if not phone:
        return Response({"error": "Phone number is required"}, status=HTTP_400_BAD_REQUEST)

    user, _ = User.objects.get_or_create(username=phone)

    profile, _ = Profile.objects.get_or_create(user=user, defaults={'phone_number': phone})

    otp = str(secrets.randbelow(9000) + 1000)
    profile.otp_code = make_password(otp)
    profile.otp_created_at = timezone.now()
    profile.otp_attempts = 0
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
        return Response({"error": "Phone and OTP required"}, status=HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(username=phone)
        profile = Profile.objects.get(user=user)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=HTTP_400_BAD_REQUEST)

    if not profile.otp_code:
        return Response({"error": "No OTP requested"}, status=HTTP_400_BAD_REQUEST)

    if timezone.now() - profile.otp_created_at > timedelta(minutes=5):
        return Response({"error": "OTP expired"}, status=HTTP_400_BAD_REQUEST)
    if profile.otp_attempts >= 3:
        profile.otp_code = None
        profile.save()
        return Response({"error": "Too many attempts. Request new OTP."}, status=HTTP_400_BAD_REQUEST)
    if check_password(code, profile.otp_code):
        profile.otp_code = None
        profile.otp_attempts = 0
        profile.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({"token":token.key})
    else:
        profile.otp_attempts += 1
        profile.save()
        return Response({"error": "Invalid OTP"}, status=HTTP_400_BAD_REQUEST)


verify_otp.throttle_scope = 'otp_verify'