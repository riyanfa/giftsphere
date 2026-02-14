from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Product, GroupGift, Wishlist


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.ReadOnlyField(source='profile.phone_number')
    avatar = serializers.ImageField(source="profile.avatar")
    class Meta:
        model = User
        fields = ['id','first_name','last_name','phone_number','avatar']
class GroupGiftSerializer(serializers.ModelSerializer):
    organizer_name = serializers.ReadOnlyField(source='organizer.username')

    class Meta:
        model = GroupGift
        fields = '__all__'

class WishlistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # The Owner
    products = ProductSerializer(many=True, read_only=True)  # The Items
    shared = UserSerializer(many=True, read_only=True)  # The Friends
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'title', 'created_at', 'products', 'shared']