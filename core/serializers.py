from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, GroupGift, Wishlist


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class GroupGiftSerializer(serializers.ModelSerializer):
    organizer_name = serializers.ReadOnlyField(source='organizer.username')

    class Meta:
        model = GroupGift
        fields = '__all__'
class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=Wishlist
        fields='__all__'
        depth=1