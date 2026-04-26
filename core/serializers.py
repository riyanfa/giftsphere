from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Product, GroupGift, Pledge, Wishlist, SecretGiftExchange, GiftAssignment


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField(method_name="get_phone_number")
    avatar = serializers.SerializerMethodField(method_name="get_avatar")

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'avatar']

    def get_phone_number(self, obj):
        return obj.profile.phone_number if hasattr(obj, 'profile') else None

    def get_avatar(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            url = obj.profile.avatar.url
            if request:
                return request.build_absolute_uri(url)
            return url  # fallback: relative path
        return None
class PledgeSerializer(serializers.ModelSerializer):
    """Serializer for individual pledges inside a Qattah."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Pledge
        fields = ['id', 'user', 'amount', 'message', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class GroupGiftSerializer(serializers.ModelSerializer):
    """Full Qattah serializer — includes progress metrics and nested data."""
    organizer = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    recipient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='recipient',
        write_only=True, required=False, allow_null=True
    )
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    participants = UserSerializer(many=True, read_only=True)
    pledges = PledgeSerializer(many=True, read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()

    class Meta:
        model = GroupGift
        fields = [
            'id', 'title',
            'invite_code',
            'organizer',
            'recipient', 'recipient_id',
            'product', 'product_id',
            'target_amount', 'collected_amount', 'remaining_amount',
            'status', 'deadline', 'days_left',
            'created_at', 'participants', 'pledges',
        ]
        read_only_fields = ['invite_code', 'organizer', 'collected_amount', 'status', 'created_at']

    def get_remaining_amount(self, obj):
        return max(obj.target_amount - obj.collected_amount, 0)

    def get_days_left(self, obj):
        """Returns whole days remaining until deadline, or None if no deadline set."""
        if not obj.deadline:
            return None
        from django.utils import timezone
        delta = obj.deadline - timezone.now()
        return max(delta.days, 0)

class WishlistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # The Owner
    products = ProductSerializer(many=True, read_only=True)  # The Items
    shared = UserSerializer(many=True, read_only=True)  # The Friends
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'title', 'visibility', 'created_at', 'products', 'shared']


class SecretGiftExchangeSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = SecretGiftExchange
        fields = [
            'id',
            'title',
            'invite_code',
            'organizer',
            'participants',
            'status',
            'created_at',
            'draw_date'
        ]
        read_only_fields = ['invite_code', 'organizer', 'status']

class GiftAssignmentSerializer(serializers.ModelSerializer):
    giver = serializers.StringRelatedField()
    receiver = serializers.StringRelatedField()

    class Meta:
        model = GiftAssignment
        fields = '__all__'
