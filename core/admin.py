from django.contrib import admin
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
    SecretGiftExchange,
    SecretGiftParticipant,
    Wishlist,
    WishlistItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'icon')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'category', 'price', 'store_name',
        'occasion', 'target_gender', 'collection_name', 'is_featured', 'is_active',
    )
    list_filter = (
        'is_active', 'is_featured', 'category', 'store_name',
        'occasion', 'target_gender', 'collection_name',
    )
    search_fields = ('name', 'description', 'interests', 'affiliate_link', 'collection_name')


@admin.register(GroupGift)
class GroupGiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organizer', 'product', 'target_amount', 'collected_amount', 'status', 'invite_code')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'invite_code', 'organizer__username', 'payment_method_note')


@admin.register(GroupGiftParticipant)
class GroupGiftParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_gift', 'user', 'status', 'joined_at', 'updated_at')
    list_filter = ('status', 'joined_at')
    search_fields = ('group_gift__title', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Pledge)
class PledgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_gift', 'user', 'amount', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('group_gift__title', 'user__username', 'message')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'visibility', 'created_at')
    list_filter = ('visibility', 'created_at')
    search_fields = ('title', 'user__username')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'wishlist', 'product', 'priority', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('wishlist__title', 'product__name', 'note')


@admin.register(SecretGiftExchange)
class SecretGiftExchangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organizer', 'status', 'invite_code', 'budget', 'created_at', 'draw_date')
    list_filter = ('status', 'created_at', 'draw_date')
    search_fields = ('title', 'invite_code', 'organizer__username')


@admin.register(SecretGiftParticipant)
class SecretGiftParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'exchange', 'user', 'status', 'joined_at', 'updated_at')
    list_filter = ('status', 'joined_at')
    search_fields = ('exchange__title', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(GiftAssignment)
class GiftAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'exchange', 'giver', 'receiver', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('exchange__title', 'giver__username', 'receiver__username')


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'event_date', 'reminder_date', 'recipient_name')
    list_filter = ('event_date', 'reminder_date')
    search_fields = ('title', 'recipient_name', 'notes', 'user__username')


@admin.register(GiftQuizAttempt)
class GiftQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'occasion', 'recipient_age', 'recipient_gender', 'budget_min', 'budget_max', 'created_at')
    list_filter = ('occasion', 'recipient_gender', 'created_at')
    search_fields = ('user__username', 'occasion', 'interests')


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'clicked_at')
    list_filter = ('clicked_at', 'product__store_name')
    search_fields = ('user__username', 'product__name')


@admin.register(InAppNotification)
class InAppNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at', 'read_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'body')
