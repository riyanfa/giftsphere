from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import (
    AffiliateClick,
    Category,
    EventReminder,
    GiftAssignment,
    GiftQuizAttempt,
    GroupGift,
    GroupGiftParticipant,
    InAppNotification,
    Pledge,
    Product,
    Profile,
    SecretGiftExchange,
    SecretGiftParticipant,
    Wishlist,
    WishlistItem,
)
from .notifications import notify_pledge_received


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
        self.assertTrue(
            SecretGiftParticipant.objects.filter(
                exchange_id=response.data["id"],
                user__username="512300000",
                status=SecretGiftParticipant.STATUS_ACCEPTED,
            ).exists()
        )

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
        self.assertTrue(
            SecretGiftParticipant.objects.filter(
                exchange__invite_code=invite_code,
                user__username="512300002",
                status=SecretGiftParticipant.STATUS_ACCEPTED,
            ).exists()
        )

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
        self.assertEqual(assignments.count(), 3)
        self.assertEqual(assignments.values('receiver_id').distinct().count(), 3)
        for assignment in assignments:
            self.assertNotEqual(assignment.giver_id, assignment.receiver_id)

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
        for assignment in assignments:
            self.assertNotEqual(assignment.giver_id, assignment.receiver_id)

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

    def test_draw_assignments_uses_only_accepted_participants(self):
        self._authenticate("512300020")
        create = self.client.post("/api/exchange/create/", {"title": "Accepted Only"}, format="json")
        exchange_id = create.data["id"]

        self._authenticate("512300021")
        self.client.post("/api/exchange/join/", {"invite_code": create.data["invite_code"]}, format="json")

        self._authenticate("512300022")
        self.client.post("/api/exchange/join/", {"invite_code": create.data["invite_code"]}, format="json")
        rejected_user = User.objects.get(username="512300022")
        SecretGiftParticipant.objects.filter(exchange_id=exchange_id, user=rejected_user).update(
            status=SecretGiftParticipant.STATUS_REJECTED
        )

        self._authenticate("512300020")
        response = self.client.post(f"/api/exchange/{exchange_id}/draw/")

        self.assertEqual(response.status_code, 200)
        assignments = GiftAssignment.objects.filter(exchange_id=exchange_id)
        self.assertEqual(assignments.count(), 2)
        self.assertFalse(assignments.filter(giver=rejected_user).exists())
        self.assertFalse(assignments.filter(receiver=rejected_user).exists())

    def test_non_organizer_cannot_draw(self):
        self._authenticate("512300030")
        create = self.client.post("/api/exchange/create/", {"title": "No Draw"}, format="json")

        self._authenticate("512300031")
        response = self.client.post(f"/api/exchange/{create.data['id']}/draw/")

        self.assertEqual(response.status_code, 403)


class GiftAssignmentConstraintTests(APITestCase):
    def test_database_prevents_duplicate_receiver_and_self_assignment(self):
        organizer = User.objects.create_user(username="constraint-org")
        giver_one = User.objects.create_user(username="constraint-giver-one")
        giver_two = User.objects.create_user(username="constraint-giver-two")
        receiver = User.objects.create_user(username="constraint-receiver")
        exchange = SecretGiftExchange.objects.create(organizer=organizer, title="Constraints")

        GiftAssignment.objects.create(exchange=exchange, giver=giver_one, receiver=receiver)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GiftAssignment.objects.create(exchange=exchange, giver=giver_two, receiver=receiver)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                GiftAssignment.objects.create(exchange=exchange, giver=giver_two, receiver=giver_two)


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
        self.assertTrue(
            GroupGiftParticipant.objects.filter(
                group_gift=group_gift,
                user__username="512399002",
                status=GroupGiftParticipant.STATUS_ACCEPTED,
            ).exists()
        )

    def test_create_qattah_creates_accepted_organizer_participant(self):
        self._authenticate("512399003")
        response = self.client.post(
            "/api/qattah/create/",
            {"title": "Organizer Gift", "product_id": self.product.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            GroupGiftParticipant.objects.filter(
                group_gift_id=response.data["id"],
                user__username="512399003",
                status=GroupGiftParticipant.STATUS_ACCEPTED,
            ).exists()
        )

    def test_rejected_participant_cannot_pledge(self):
        self._authenticate("512399004")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "Rejected Gift", "product_id": self.product.id},
            format="json",
        )
        group_gift = GroupGift.objects.get(id=create_response.data["id"])

        self._authenticate("512399005")
        user = User.objects.get(username="512399005")
        GroupGiftParticipant.objects.create(
            group_gift=group_gift,
            user=user,
            status=GroupGiftParticipant.STATUS_REJECTED,
        )
        response = self.client.post(
            f"/api/qattah/{group_gift.id}/pledge/",
            {"amount": "10.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_accepted_participant_can_pledge_with_default_status(self):
        self._authenticate("512399006")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "Default Pledge", "product_id": self.product.id},
            format="json",
        )

        self._authenticate("512399007")
        self.client.post("/api/qattah/join/", {"invite_code": create_response.data["invite_code"]}, format="json")
        response = self.client.post(
            f"/api/qattah/{create_response.data['id']}/pledge/",
            {"amount": "25.00", "message": "Happy birthday"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        pledge = Pledge.objects.get(group_gift_id=create_response.data["id"], user__username="512399007")
        self.assertEqual(pledge.status, Pledge.STATUS_PLEDGED)
        self.assertEqual(response.data["pledge"]["status"], Pledge.STATUS_PLEDGED)

    def test_pledge_status_can_be_paid_externally(self):
        self._authenticate("512399008")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "External Pledge", "product_id": self.product.id},
            format="json",
        )

        self._authenticate("512399009")
        self.client.post("/api/qattah/join/", {"invite_code": create_response.data["invite_code"]}, format="json")
        response = self.client.post(
            f"/api/qattah/{create_response.data['id']}/pledge/",
            {"amount": "30.00", "status": Pledge.STATUS_PAID_EXTERNALLY},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["pledge"]["status"], Pledge.STATUS_PAID_EXTERNALLY)

    def test_duplicate_pledge_returns_409(self):
        self._authenticate("512399010")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "Duplicate Pledge", "product_id": self.product.id},
            format="json",
        )

        self._authenticate("512399011")
        self.client.post("/api/qattah/join/", {"invite_code": create_response.data["invite_code"]}, format="json")
        self.client.post(f"/api/qattah/{create_response.data['id']}/pledge/", {"amount": "20.00"}, format="json")
        response = self.client.post(
            f"/api/qattah/{create_response.data['id']}/pledge/",
            {"amount": "20.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_qattah_completes_when_collected_amount_reaches_target(self):
        self._authenticate("512399012")
        create_response = self.client.post(
            "/api/qattah/create/",
            {"title": "Complete Gift", "product_id": self.product.id},
            format="json",
        )

        self._authenticate("512399013")
        self.client.post("/api/qattah/join/", {"invite_code": create_response.data["invite_code"]}, format="json")
        response = self.client.post(
            f"/api/qattah/{create_response.data['id']}/pledge/",
            {"amount": "299.00"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        group_gift = GroupGift.objects.get(id=create_response.data["id"])
        self.assertEqual(group_gift.status, "COMPLETED")

    def test_qattah_payment_note_visibility(self):
        payment_note = "Transfer to STC Pay 05xxxxxxxx"

        self._authenticate("512399014")
        create_response = self.client.post(
            "/api/qattah/create/",
            {
                "title": "Graduation Qattah",
                "product_id": self.product.id,
                "payment_method_note": payment_note,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["payment_method_note"], payment_note)
        group_gift = GroupGift.objects.get(id=create_response.data["id"])
        self.assertEqual(group_gift.payment_method_note, payment_note)

        organizer_detail = self.client.get(f"/api/qattah/{group_gift.id}/")
        self.assertEqual(organizer_detail.status_code, 200)
        self.assertEqual(organizer_detail.data["payment_method_note"], payment_note)

        self._authenticate("512399015")
        self.client.post("/api/qattah/join/", {"invite_code": create_response.data["invite_code"]}, format="json")
        participant_detail = self.client.get(f"/api/qattah/{group_gift.id}/")
        self.assertEqual(participant_detail.status_code, 200)
        self.assertEqual(participant_detail.data["payment_method_note"], payment_note)

        self._authenticate("512399016")
        non_participant_detail = self.client.get(f"/api/qattah/{group_gift.id}/")
        self.assertEqual(non_participant_detail.status_code, 200)
        self.assertEqual(non_participant_detail.data["payment_method_note"], "")

        public_list = self.client.get("/api/qattah/")
        listed_qattah = next(item for item in public_list.data if item["id"] == group_gift.id)
        self.assertEqual(listed_qattah["payment_method_note"], "")


class ProductAffiliateQuizTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="product-user")
        self.client.force_authenticate(self.user)
        self.category = Category.objects.create(name="Toys", icon="gift")
        self.electronics_category = Category.objects.create(name="Electronics", icon="headphones")
        self.matching_product = Product.objects.create(
            name="Birthday LEGO Set",
            category=self.category,
            price="150.00",
            description="Creative building set",
            image_url="https://example.com/lego.jpg",
            affiliate_link="https://example.com/lego",
            store_name="Amazon SA",
            occasion="birthday",
            target_gender="any",
            min_age=8,
            max_age=14,
            interests="building, toys",
            is_active=True,
            is_featured=True,
            collection_name="Gifts for Students",
        )
        self.inactive_product = Product.objects.create(
            name="Inactive Drone",
            category=self.category,
            price="200.00",
            description="Hidden inactive product",
            image_url="https://example.com/drone.jpg",
            affiliate_link="https://example.com/drone",
            store_name="Noon",
            is_active=False,
            is_featured=True,
            collection_name="Gifts for Gamers",
        )
        self.no_collection_product = Product.objects.create(
            name="Active No Collection",
            category=self.category,
            price="90.00",
            description="Active but not grouped",
            image_url="https://example.com/plain.jpg",
            affiliate_link="https://example.com/plain",
            store_name="Amazon SA",
            is_active=True,
        )
        self.electronics_product = Product.objects.create(
            name="Gaming Headphones",
            category=self.electronics_category,
            price="250.00",
            description="Wireless headset with immersive sound",
            image_url="https://example.com/headphones.jpg",
            affiliate_link="https://example.com/headphones",
            store_name="Noon",
            occasion="graduation",
            interests="gaming, music",
            is_active=True,
        )

    def _product_ids(self, response):
        return [product["id"] for product in response.data["results"]]

    def test_get_products_returns_only_active_products_by_default(self):
        response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, 200)
        names = [item["name"] for item in response.data["results"]]
        self.assertIn(self.matching_product.name, names)
        self.assertNotIn(self.inactive_product.name, names)

    def test_get_products_searches_by_product_name(self):
        response = self.client.get("/api/products/", {"search": "headphones"})

        self.assertEqual(response.status_code, 200)
        product_ids = self._product_ids(response)
        self.assertIn(self.electronics_product.id, product_ids)
        self.assertNotIn(self.matching_product.id, product_ids)

    def test_get_products_searches_by_category_name(self):
        response = self.client.get("/api/products/", {"search": "Electronics"})

        self.assertEqual(response.status_code, 200)
        product_ids = self._product_ids(response)
        self.assertIn(self.electronics_product.id, product_ids)
        self.assertNotIn(self.matching_product.id, product_ids)

    def test_get_products_filters_by_category_id(self):
        response = self.client.get("/api/products/", {"category": str(self.electronics_category.id)})

        self.assertEqual(response.status_code, 200)
        product_ids = self._product_ids(response)
        self.assertEqual(product_ids, [self.electronics_product.id])

    def test_get_products_filters_by_category_name(self):
        response = self.client.get("/api/products/", {"category": "Electronics"})

        self.assertEqual(response.status_code, 200)
        product_ids = self._product_ids(response)
        self.assertEqual(product_ids, [self.electronics_product.id])

    def test_get_products_filters_by_budget_range(self):
        response = self.client.get("/api/products/", {"budget_min": "100", "budget_max": "200"})

        self.assertEqual(response.status_code, 200)
        product_ids = self._product_ids(response)
        self.assertIn(self.matching_product.id, product_ids)
        self.assertNotIn(self.no_collection_product.id, product_ids)
        self.assertNotIn(self.electronics_product.id, product_ids)
        self.assertNotIn(self.inactive_product.id, product_ids)

    def test_get_products_rejects_invalid_budget(self):
        response = self.client.get("/api/products/", {"budget_min": "not-a-number"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "budget_min must be a valid number.")

    def test_affiliate_click_endpoint_creates_click_and_returns_link(self):
        response = self.client.post(f"/api/products/{self.matching_product.id}/affiliate-click/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["affiliate_link"], self.matching_product.affiliate_link)
        self.assertTrue(
            AffiliateClick.objects.filter(user=self.user, product=self.matching_product).exists()
        )

    def test_quiz_attempt_creates_attempt_and_returns_matching_products(self):
        response = self.client.post(
            "/api/products/quiz/",
            {
                "occasion": "birthday",
                "recipient_age": 10,
                "recipient_gender": "any",
                "interests": "building",
                "budget_min": "100.00",
                "budget_max": "200.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(GiftQuizAttempt.objects.count(), 1)
        recommended_ids = [product["id"] for product in response.data["recommended_products"]]
        self.assertIn(self.matching_product.id, recommended_ids)
        self.assertNotIn(self.inactive_product.id, recommended_ids)

    def test_collections_endpoint_returns_only_active_products_with_collection_name(self):
        response = self.client.get("/api/products/collections/")

        self.assertEqual(response.status_code, 200)
        collections = {collection["name"]: collection["products"] for collection in response.data["collections"]}
        self.assertIn("Gifts for Students", collections)
        self.assertNotIn("Gifts for Gamers", collections)

        product_ids = [product["id"] for product in collections["Gifts for Students"]]
        self.assertIn(self.matching_product.id, product_ids)
        self.assertNotIn(self.inactive_product.id, product_ids)
        self.assertNotIn(self.no_collection_product.id, product_ids)

    def test_featured_endpoint_returns_only_active_featured_products(self):
        response = self.client.get("/api/products/featured/")

        self.assertEqual(response.status_code, 200)
        product_ids = [product["id"] for product in response.data]
        self.assertIn(self.matching_product.id, product_ids)
        self.assertNotIn(self.inactive_product.id, product_ids)
        self.assertNotIn(self.no_collection_product.id, product_ids)


class EventReminderTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="reminder-user")
        self.other_user = User.objects.create_user(username="other-reminder-user")
        self.client.force_authenticate(self.user)
        self.event_date = timezone.now() + timedelta(days=7)
        self.reminder_date = timezone.now() + timedelta(days=3)

    def test_authenticated_user_can_create_reminder(self):
        response = self.client.post(
            "/api/reminders/create/",
            {
                "title": "Mom birthday",
                "event_date": self.event_date.isoformat(),
                "reminder_date": self.reminder_date.isoformat(),
                "recipient_name": "Mom",
                "notes": "Find a gift",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Mom birthday")
        self.assertTrue(EventReminder.objects.filter(user=self.user, title="Mom birthday").exists())

    def test_user_can_list_only_their_own_reminders(self):
        EventReminder.objects.create(
            user=self.user,
            title="Mine",
            event_date=self.event_date,
            reminder_date=self.reminder_date,
        )
        EventReminder.objects.create(
            user=self.other_user,
            title="Other",
            event_date=self.event_date,
            reminder_date=self.reminder_date,
        )

        response = self.client.get("/api/reminders/")

        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data]
        self.assertEqual(titles, ["Mine"])

    def test_reminder_date_after_event_date_returns_400(self):
        response = self.client.post(
            "/api/reminders/create/",
            {
                "title": "Invalid",
                "event_date": self.event_date.isoformat(),
                "reminder_date": (self.event_date + timedelta(days=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("reminder_date", response.data)

    def test_user_cannot_update_or_delete_another_users_reminder(self):
        reminder = EventReminder.objects.create(
            user=self.other_user,
            title="Other",
            event_date=self.event_date,
            reminder_date=self.reminder_date,
        )

        update_response = self.client.patch(
            f"/api/reminders/{reminder.id}/",
            {"title": "Changed"},
            format="json",
        )
        delete_response = self.client.delete(f"/api/reminders/{reminder.id}/")

        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        reminder.refresh_from_db()
        self.assertEqual(reminder.title, "Other")

    def test_upcoming_endpoint_returns_future_reminders(self):
        future_reminder = EventReminder.objects.create(
            user=self.user,
            title="Future",
            event_date=self.event_date,
            reminder_date=self.reminder_date,
        )
        EventReminder.objects.create(
            user=self.user,
            title="Past",
            event_date=timezone.now() + timedelta(days=1),
            reminder_date=timezone.now() - timedelta(days=1),
        )

        response = self.client.get("/api/reminders/upcoming/")

        self.assertEqual(response.status_code, 200)
        reminder_ids = [item["id"] for item in response.data]
        self.assertEqual(reminder_ids, [future_reminder.id])


class WishlistTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="wishlist-user")
        self.client.force_authenticate(self.user)
        self.category = Category.objects.create(name="Books", icon="book")
        self.product = Product.objects.create(
            name="Gift Book",
            category=self.category,
            price="45.00",
            description="Book",
            image_url="https://example.com/book.jpg",
            affiliate_link="https://example.com/book",
            store_name="Example Store",
        )
        self.wishlist = Wishlist.objects.create(user=self.user, title="Books")

    def test_wishlist_duplicate_add_returns_409_and_remove_works(self):
        first = self.client.post(
            "/api/wishlist/add_product/",
            {"wishlist_id": self.wishlist.id, "product_id": self.product.id},
            format="json",
        )
        duplicate = self.client.post(
            "/api/wishlist/add_product/",
            {"wishlist_id": self.wishlist.id, "product_id": self.product.id},
            format="json",
        )
        remove = self.client.post(
            "/api/wishlist/remove_product/",
            {"wishlist_id": self.wishlist.id, "product_id": self.product.id},
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(remove.status_code, 200)
        self.assertFalse(WishlistItem.objects.filter(wishlist=self.wishlist, product=self.product).exists())


class NotificationInboxTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="notification-user")
        self.other_user = User.objects.create_user(username="other-notification-user")
        self.client.force_authenticate(self.user)

    def test_notification_helper_creates_inbox_record(self):
        category = Category.objects.create(name="Tech", icon="gift")
        product = Product.objects.create(
            name="Speaker",
            category=category,
            price="120.00",
            description="Portable speaker",
            image_url="https://example.com/speaker.jpg",
            affiliate_link="https://example.com/speaker",
            store_name="Amazon SA",
        )
        group_gift = GroupGift.objects.create(
            organizer=self.user,
            product=product,
            title="Speaker Qattah",
            target_amount=product.price,
        )
        pledge = Pledge.objects.create(
            group_gift=group_gift,
            user=self.other_user,
            amount="25.00",
        )

        notify_pledge_received(group_gift, pledge)

        notification = InAppNotification.objects.get(user=self.user)
        self.assertEqual(notification.notification_type, "PLEDGE_RECEIVED")
        self.assertEqual(notification.data["qattah_id"], str(group_gift.id))
        self.assertFalse(notification.is_read)

    def test_notifications_endpoint_lists_only_current_user_notifications(self):
        own_notification = InAppNotification.objects.create(
            user=self.user,
            title="Mine",
            body="Visible",
            notification_type="TEST",
        )
        InAppNotification.objects.create(
            user=self.other_user,
            title="Other",
            body="Hidden",
            notification_type="TEST",
        )

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["notifications"]), 1)
        self.assertEqual(response.data["notifications"][0]["id"], own_notification.id)

    def test_mark_notification_read(self):
        notification = InAppNotification.objects.create(
            user=self.user,
            title="Unread",
            body="Needs read state",
            notification_type="TEST",
        )

        response = self.client.patch(f"/api/notifications/{notification.id}/read/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_read"])
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_cannot_mark_another_users_notification_read(self):
        notification = InAppNotification.objects.create(
            user=self.other_user,
            title="Other",
            body="Hidden",
            notification_type="TEST",
        )

        response = self.client.patch(f"/api/notifications/{notification.id}/read/")

        self.assertEqual(response.status_code, 404)
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)
