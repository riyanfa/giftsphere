from rest_framework import serializers
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
    shared = ProductSerializer(many=True,read_only=True,allow_null=True)
    #products = UserSerializer(many=True,read_only=True,allow_null=True)
    class Meta:
        model=Wishlist
        fields = ['id', 'user', 'title', 'created_at', 'products', 'shared']
