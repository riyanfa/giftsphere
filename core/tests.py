from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Profile


class AuthFlowTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_request_otp_rejects_invalid_phone(self):
        response = self.client.post(
            "/api/login/request/",
            {"phone": "12345"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Wrong phone number")

    def test_request_otp_creates_profile_and_hashes_otp(self):
        response = self.client.post(
            "/api/login/request/",
            {"phone": "512345678"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("debug_otp", response.data)
        self.assertEqual(response.data["message"], "OTP Sent Successfully")

        profile = Profile.objects.select_related("user").get(phone_number="512345678")
        self.assertIsNotNone(profile.otp_code)
        self.assertTrue(check_password(response.data["debug_otp"], profile.otp_code))
        self.assertEqual(profile.otp_attempts, 0)

    def test_verify_otp_returns_token_and_clears_otp(self):
        request_response = self.client.post(
            "/api/login/request/",
            {"phone": "512345679"},
            format="json",
        )
        otp = request_response.data["debug_otp"]

        verify_response = self.client.post(
            "/api/login/verify/",
            {"phone": "512345679", "otp": otp},
            format="json",
        )

        self.assertEqual(verify_response.status_code, 200)
        self.assertIn("token", verify_response.data)

        profile = Profile.objects.get(phone_number="512345679")
        self.assertIsNone(profile.otp_code)
        self.assertEqual(profile.otp_attempts, 0)
        self.assertTrue(Token.objects.filter(user=profile.user).exists())

    def test_verify_otp_wrong_code_increments_attempts(self):
        self.client.post("/api/login/request/", {"phone": "512345670"}, format="json")

        verify_response = self.client.post(
            "/api/login/verify/",
            {"phone": "512345670", "otp": "9999"},
            format="json",
        )

        self.assertEqual(verify_response.status_code, 400)
        self.assertEqual(verify_response.data["error"], "Invalid OTP")

        profile = Profile.objects.get(phone_number="512345670")
        self.assertEqual(profile.otp_attempts, 1)


class ProfileEndpointTests(APITestCase):
    def setUp(self):
        cache.clear()

    def _authenticate(self, phone="512345671"):
        request_response = self.client.post(
            "/api/login/request/",
            {"phone": phone},
            format="json",
        )
        otp = request_response.data["debug_otp"]
        verify_response = self.client.post(
            "/api/login/verify/",
            {"phone": phone, "otp": otp},
            format="json",
        )
        token = verify_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")

    def test_set_full_name_updates_user_names(self):
        self._authenticate()

        response = self.client.post(
            "/api/setname/",
            {"first_name": "Riyan", "last_name": "A"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Name updated successfully")

        user = User.objects.get(username="512345671")
        self.assertEqual(user.first_name, "Riyan")
        self.assertEqual(user.last_name, "A")
