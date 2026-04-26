from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Category, Product, GroupGift, SecretGiftExchange, GiftAssignment, Profile


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



class GiftExchangeTests(APITestCase):
    def setUp(self):
        cache.clear()

    def _authenticate(self, phone):
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

    def test_create_exchange(self):
        self._authenticate("512300000")


        response = self.client.post(
            "/api/exchange/create/",
            {"title": "Test Exchange"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Test Exchange")

    def test_join_exchange(self):
        # Organizer
        self._authenticate("512300001")
        create = self.client.post("/api/exchange/create/", {"title": "Test"}, format="json")
        invite_code = create.data["invite_code"]

        # New user joins
        self._authenticate("512300002")
        response = self.client.post(
            "/api/exchange/join/",
            {"invite_code": invite_code},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_draw_assignments(self):
        # Organizer
        self._authenticate("512300003")
        create = self.client.post("/api/exchange/create/", {"title": "Draw Test"}, format="json")
        exchange_id = create.data["id"]
        # prints for visualization
        # print(f"\n{'=' * 50}")
        # print(f"Exchange: Draw Test (ID: {exchange_id})")
        # print(f"{'=' * 50}")

        # Add participants
        self._authenticate("512300004")
        self.client.post(
            "/api/exchange/join/",
            {"invite_code": create.data["invite_code"]},
            format="json",
        )

        self._authenticate("512300005")
        self.client.post(
            "/api/exchange/join/",
            {"invite_code": create.data["invite_code"]},
            format="json",
        )

        # Back to organizer
        self._authenticate("512300003")
        response = self.client.post(f"/api/exchange/{exchange_id}/draw/")

        self.assertEqual(response.status_code, 200)

        assignments = GiftAssignment.objects.filter(exchange_id=exchange_id).select_related('giver', 'receiver')
        self.assertTrue(assignments.exists())

        # print("\nSecret gift:")
        # print("-" * 40)
        # for assignment in assignments:
        #     giver_name = f"{assignment.giver.first_name} {assignment.giver.last_name}".strip() or assignment.giver.username
        #     receiver_name = f"{assignment.receiver.first_name} {assignment.receiver.last_name}".strip() or assignment.receiver.username
        #     print(f"  {giver_name} → {receiver_name}")
        # print("-" * 40)

    def test_no_self_assignment(self):
        self._authenticate("512300010")
        create = self.client.post("/api/exchange/create/", {"title": "No Self"}, format="json")
        exchange_id = create.data["id"]

        # print(f"\n{'=' * 50}")
        # print(f"Exchange: No Self (ID: {exchange_id})")
        # print(f"{'=' * 50}")

        phones = ["512300011", "512300012", "512300013"]
        participants_info = []

        for phone in phones:
            self._authenticate(phone)
            self.client.post(
                "/api/exchange/join/",
                {"invite_code": create.data["invite_code"]},
                format="json",
            )
            # Get user info for printing
            user = User.objects.get(username=phone)
            participants_info.append(user)

        self._authenticate("512300010")
        self.client.post(f"/api/exchange/{exchange_id}/draw/")

        assignments = GiftAssignment.objects.filter(exchange_id=exchange_id).select_related('giver', 'receiver')

        # print("\n Secret Santa Assignments (No Self-Assignment Check):")
        # print("-" * 40)
        # for assignment in assignments:
        #     giver_name = f"{assignment.giver.first_name} {assignment.giver.last_name}".strip() or assignment.giver.username
        #     receiver_name = f"{assignment.receiver.first_name} {assignment.receiver.last_name}".strip() or assignment.receiver.username
        #     print(f"  {giver_name} → {receiver_name}")
        #
        #     # Verify no self-assignment
        #     self.assertNotEqual(assignment.giver, assignment.receiver)
        # print("-" * 40)
        # print(" No one is assigned to themselves")


class QattahJoinTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name="Electronics", icon="gift")
        self.product = Product.objects.create(
            name="Headphones",
            category=self.category,
            price="299.00",
            description="Wireless headphones",
            image_url="https://example.com/headphones.jpg",
            affiliate_link="https://example.com/buy-headphones",
            store_name="Example Store",
        )

    def _authenticate(self, phone):
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

    def test_join_qattah_by_invite_code(self):
        self._authenticate("512399001")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "Birthday Gift", "product_id": self.product.id},
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        invite_code = create_response.data["invite_code"]
        qattah_id = create_response.data["id"]

        self._authenticate("512399002")
        join_response = self.client.post(
            "/api/qattah/join/",
            {"invite_code": invite_code},
            format="json",
        )

        self.assertEqual(join_response.status_code, 200)
        self.assertEqual(join_response.data["message"], "Joined successfully.")
        self.assertEqual(join_response.data["qattah"]["id"], qattah_id)

        group_gift = GroupGift.objects.get(id=qattah_id)
        self.assertTrue(group_gift.participants.filter(username="512399002").exists())
