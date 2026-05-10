from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string


# 1. USER PROFILE (OTP & Phone)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True,db_index=True)
    otp_code = models.CharField(max_length=128, blank=True, null=True)
    otp_attempts = models.IntegerField(default=0)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # Added for UI

    def __str__(self):
        return self.phone_number


# 2. CATEGORY (For filtering)
class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="star")  # Flutter icon name

    def __str__(self):
        return self.name


# 3. PRODUCT (Affiliate - No Stock/Shipping)
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    image_url = models.URLField()
    occasion = models.CharField(max_length=100, blank=True)
    target_gender = models.CharField(max_length=20, blank=True)
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    interests = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    collection_name = models.CharField(max_length=100, blank=True)

    # KEY FEATURE: The Link to Amazon/Noon
    affiliate_link = models.URLField()
    store_name = models.CharField(max_length=50, default="Amazon SA")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

def generate_numeric_code():
    return get_random_string(length=8, allowed_chars='0123456789')

# 4. GROUP GIFT (The Event)
class GroupGift(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    organizer = models.ForeignKey(User, related_name='organized_gifts', on_delete=models.CASCADE)
    # Who the gift is actually for (the birthday person, the graduate, etc.)
    recipient = models.ForeignKey(
        User, related_name='received_gifts',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    collected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method_note = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    deadline = models.DateTimeField(null=True, blank=True)  # "3 days left" for the Flutter UI
    created_at = models.DateTimeField(auto_now_add=True)
    invite_code = models.CharField(max_length=8, default=generate_numeric_code, unique=True)
    participants = models.ManyToManyField(
        User,
        through='GroupGiftParticipant',
        related_name='joined_qattahs',
        blank=True,
    )

    def __str__(self):
        return f"{self.title} - {self.status}"


class GroupGiftParticipant(models.Model):
    STATUS_INVITED = 'INVITED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_LEFT = 'LEFT'
    STATUS_CHOICES = [
        (STATUS_INVITED, 'Invited'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_LEFT, 'Left'),
    ]

    group_gift = models.ForeignKey(
        GroupGift,
        related_name='participant_statuses',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, related_name='qattah_participations', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INVITED)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('group_gift', 'user')

    def __str__(self):
        return f"{self.user} in {self.group_gift}: {self.status}"


# 5. PLEDGE (The Contribution - CRITICAL FOR SOCIAL)
class Pledge(models.Model):
    STATUS_PLEDGED = 'PLEDGED'
    STATUS_PAID_EXTERNALLY = 'PAID_EXTERNALLY'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_PLEDGED, 'Pledged'),
        (STATUS_PAID_EXTERNALLY, 'Paid externally'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    group_gift = models.ForeignKey(GroupGift, related_name='pledges', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PLEDGED)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional: Message ("Happy Birthday!")
    message = models.TextField(blank=True, null=True)

    class Meta:
        # One pledge per user per Qattah — mirrors the unique_together on GiftAssignment
        unique_together = ('group_gift', 'user')

    def __str__(self):
        return f"{self.user.username} paid {self.amount}"


class Wishlist(models.Model):
    VISIBILITY_CHOICES = [('PRIVATE', 'Private'), ('PUBLIC', 'Public'), ('SHARED', 'Shared')]
    user = models.ForeignKey(User, related_name='wishlists', on_delete=models.CASCADE)
    title = models.CharField(max_length=100, default="My Wishlist")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='PRIVATE')
    created_at = models.DateTimeField(auto_now_add=True)

    # 3. Link to Products (Wishlist has many Products)
    products = models.ManyToManyField(
        Product,
        through='WishlistItem',
        related_name='wishlisted_by',
        blank=True,
    )
    shared = models.ManyToManyField(User, related_name="shared_wishlists", blank=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist: {self.title}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='wishlist_items', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    priority = models.PositiveIntegerField(default=0)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ('wishlist', 'product')

    def __str__(self):
        return f"{self.product} in {self.wishlist}"


class SecretGiftExchange(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed')
    ]

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_exchanges')
    title = models.CharField(max_length=200)

    participants = models.ManyToManyField(
        User,
        through='SecretGiftParticipant',
        related_name='gift_exchanges',
        blank=True,
    )
    invite_code = models.CharField(max_length=8, default=generate_numeric_code, unique=True)
    budget = models.DecimalField(max_digits=8, decimal_places=2, default=100)


    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    draw_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class SecretGiftParticipant(models.Model):
    STATUS_INVITED = 'INVITED'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_LEFT = 'LEFT'
    STATUS_CHOICES = [
        (STATUS_INVITED, 'Invited'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_LEFT, 'Left'),
    ]

    exchange = models.ForeignKey(
        SecretGiftExchange,
        related_name='participant_statuses',
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, related_name='secret_gift_participations', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_INVITED)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('exchange', 'user')

    def __str__(self):
        return f"{self.user} in {self.exchange}: {self.status}"


class GiftAssignment(models.Model):
    exchange = models.ForeignKey(SecretGiftExchange, related_name='assignments', on_delete=models.CASCADE)

    giver = models.ForeignKey(User, related_name='giving_assignments', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='receiving_assignments', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['exchange', 'giver'], name='unique_assignment_giver_per_exchange'),
            models.UniqueConstraint(fields=['exchange', 'receiver'], name='unique_assignment_receiver_per_exchange'),
            models.CheckConstraint(
                condition=~models.Q(giver=models.F('receiver')),
                name='gift_assignment_no_self_assignment',
            ),
        ]

    def __str__(self):
        return f"{self.giver} → {self.receiver}"


class EventReminder(models.Model):
    user = models.ForeignKey(User, related_name='event_reminders', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    event_date = models.DateTimeField()
    reminder_date = models.DateTimeField()
    recipient_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} for {self.user}"


class GiftQuizAttempt(models.Model):
    user = models.ForeignKey(User, related_name='gift_quiz_attempts', on_delete=models.CASCADE)
    occasion = models.CharField(max_length=100)
    recipient_age = models.PositiveIntegerField()
    recipient_gender = models.CharField(max_length=20)
    interests = models.CharField(max_length=255)
    budget_min = models.DecimalField(max_digits=10, decimal_places=2)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} quiz for {self.occasion}"


class AffiliateClick(models.Model):
    user = models.ForeignKey(
        User,
        related_name='affiliate_clicks',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product = models.ForeignKey(Product, related_name='affiliate_clicks', on_delete=models.CASCADE)
    clicked_at = models.DateTimeField(auto_now_add=True)
# /api/exchange/13213131/accept
    def __str__(self):
        return f"{self.product} clicked by {self.user or 'anonymous'}"


class InAppNotification(models.Model):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    body = models.TextField()
    notification_type = models.CharField(max_length=50, blank=True)
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user}"
