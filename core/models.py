from django.db import models
from django.contrib.auth.models import User


# 1. USER PROFILE (OTP & Phone)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True,db_index=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
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

    # KEY FEATURE: The Link to Amazon/Noon
    affiliate_link = models.URLField()
    store_name = models.CharField(max_length=50, default="Amazon SA")

    def __str__(self):
        return self.name


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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    deadline = models.DateTimeField(null=True, blank=True)  # "3 days left" for the Flutter UI
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.status}"


# 5. PLEDGE (The Contribution - CRITICAL FOR SOCIAL)
class Pledge(models.Model):
    group_gift = models.ForeignKey(GroupGift, related_name='pledges', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
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
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)
    shared = models.ManyToManyField(User, related_name="shared_wishlists", blank=True)

    def __str__(self):
        return f"{self.user.username}'s Wishlist: {self.title}"


class SecretGiftExchange(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed')
    ]

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_exchanges')
    title = models.CharField(max_length=200)

    participants = models.ManyToManyField(User, related_name='gift_exchanges')
    budget = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    draw_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class GiftAssignment(models.Model):
    exchange = models.ForeignKey(SecretGiftExchange, related_name='assignments', on_delete=models.CASCADE)

    giver = models.ForeignKey(User, related_name='giving_assignments', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='receiving_assignments', on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('exchange', 'giver')

    def __str__(self):
        return f"{self.giver} → {self.receiver}"