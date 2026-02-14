from django.db import models
from django.contrib.auth.models import User


# 1. USER PROFILE (OTP & Phone)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_attempts=models.IntegerField(default=0)
    otp_created_at=models.DateTimeField(null=True,blank=True)
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
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('COMPLETED', 'Completed')]

    organizer = models.ForeignKey(User, related_name='organized_gifts', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)

    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    collected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
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


    def __str__(self):
        return f"{self.user.username} paid {self.amount}"
class Wishlist(models.Model):
    VISIBILITY_CHOICES = [('PRIVATE', 'Private'), ('PUBLIC', 'Public'),('SHARED','Shared')]
    # 1. Link to User (User has many Wishlists)
    user = models.ForeignKey(User, related_name='wishlists', on_delete=models.CASCADE)

    # 2. Basic Info
    title = models.CharField(max_length=100, default="My Wishlist")
    created_at = models.DateTimeField(auto_now_add=True)

    # 3. Link to Products (Wishlist has many Products)
    products = models.ManyToManyField(Product, related_name='wishlisted_by', blank=True)
    shared =models.ManyToManyField(User,related_name="shared_wishlists",blank=True)
def __str__(self):
    return f"{self.user.username} paid {self.amount}"