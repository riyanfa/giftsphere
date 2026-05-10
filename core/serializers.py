from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    AffiliateClick,
    EventReminder,
    GiftAssignment,
    GiftQuizAttempt,
    GroupGift,
    GroupGiftParticipant,
    InAppNotification,
    Pledge,
    Product,
    SecretGiftExchange,
    SecretGiftParticipant,
    Wishlist,
    WishlistItem,
    Profile
)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.SerializerMethodField(method_name="get_phone_number")
    avatar = serializers.SerializerMethodField(method_name="get_avatar")

    class Meta:
        model = User
        fields = ['id',
                  'first_name',
                  'last_name',
                  'phone_number',
                  'avatar']

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
class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'bank_name',
            'iban',
            'account_holder_name',
        ]
class PledgeSerializer(serializers.ModelSerializer):
    """Serializer for individual pledges inside a Qattah."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Pledge
        fields = ['id', 'user', 'amount', 'status', 'message', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class GroupGiftParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GroupGiftParticipant
        fields = ['id', 'user', 'status', 'joined_at', 'updated_at']
        read_only_fields = fields


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
    participant_details = GroupGiftParticipantSerializer(source='participant_statuses', many=True, read_only=True)
    pledges = PledgeSerializer(many=True, read_only=True)
    remaining_amount = serializers.SerializerMethodField()
    days_left = serializers.SerializerMethodField()
    payment_method_note = serializers.SerializerMethodField()

    class Meta:
        model = GroupGift
        fields = [
            'id', 'title',
            'invite_code',
            'organizer',
            'recipient', 'recipient_id',
            'product', 'product_id',
            'target_amount', 'collected_amount', 'remaining_amount',
            'payment_method_note',
            'status', 'deadline', 'days_left',
            'created_at', 'participants', 'participant_details', 'pledges',
        ]
        read_only_fields = ['invite_code', 'organizer', 'collected_amount', 'status', 'created_at']

    def get_payment_method_note(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or not user.is_authenticated:
            return ''

        if obj.organizer_id == user.id:
            return obj.payment_method_note

        prefetched = getattr(obj, '_prefetched_objects_cache', {}).get('participant_statuses')
        if prefetched is not None:
            is_accepted = any(
                participant.user_id == user.id and participant.status == GroupGiftParticipant.STATUS_ACCEPTED
                for participant in prefetched
            )
        else:
            is_accepted = obj.participant_statuses.filter(
                user=user,
                status=GroupGiftParticipant.STATUS_ACCEPTED,
            ).exists()

        return obj.payment_method_note if is_accepted else ''

    def get_remaining_amount(self, obj):
        return max(obj.target_amount - obj.collected_amount, 0)

    def get_days_left(self, obj):
        """Returns whole days remaining until deadline, or None if no deadline set."""
        if not obj.deadline:
            return None
        from django.utils import timezone
        delta = obj.deadline - timezone.now()
        return max(delta.days, 0)

class PaymentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'bank_name',
            'iban',
            'account_holder_name',
        ]

class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'added_at', 'priority', 'note']
        read_only_fields = fields


class WishlistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # The Owner
    products = ProductSerializer(many=True, read_only=True)  # The Items
    item_details = WishlistItemSerializer(source='items', many=True, read_only=True)
    shared = UserSerializer(many=True, read_only=True)  # The Friends
    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'title', 'visibility', 'created_at', 'products', 'item_details', 'shared']


class SecretGiftParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = SecretGiftParticipant
        fields = ['id', 'user', 'status', 'joined_at', 'updated_at']
        read_only_fields = fields


class SecretGiftExchangeSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    participants = UserSerializer(many=True, read_only=True)
    participant_details = SecretGiftParticipantSerializer(source='participant_statuses', many=True, read_only=True)

    class Meta:
        model = SecretGiftExchange
        fields = [
            'id',
            'title',
            'invite_code',
            'organizer',
            'participants',
            'participant_details',
            'status',
            'created_at',
            'draw_date',
            'budget'
        ]
        read_only_fields = ['invite_code', 'organizer', 'status']

class GiftAssignmentSerializer(serializers.ModelSerializer):
    giver = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = GiftAssignment
        fields = ['id', 'exchange', 'giver', 'receiver', 'created_at']
        read_only_fields = fields


class EventReminderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EventReminder
        fields = [
            'id', 'user', 'title', 'event_date', 'reminder_date',
            'recipient_name', 'notes', 'created_at', 'updated_at',
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def validate(self, attrs):
        event_date = attrs.get('event_date', getattr(self.instance, 'event_date', None))
        reminder_date = attrs.get('reminder_date', getattr(self.instance, 'reminder_date', None))

        if event_date and reminder_date and reminder_date > event_date:
            raise serializers.ValidationError({
                'reminder_date': 'Reminder date cannot be after event date.'
            })

        return attrs


class GiftQuizAttemptSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GiftQuizAttempt
        fields = [
            'id', 'user', 'occasion', 'recipient_age', 'recipient_gender',
            'interests', 'budget_min', 'budget_max', 'created_at',
        ]
        read_only_fields = ['user', 'created_at']


class AffiliateClickSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = AffiliateClick
        fields = ['id', 'user', 'product', 'clicked_at']
        read_only_fields = fields


class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = [
            'id', 'title', 'body', 'notification_type',
            'data', 'is_read', 'created_at', 'read_at',
        ]
        read_only_fields = fields
