from django.urls import path
from . import views


urlpatterns = [
    # ── Authentication ────────────────────────────────────────────────────────
    path('login/request/', views.auth.request_otp),
    path('login/verify/', views.auth.verify_otp),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile/me/', views.get_current_user),
    path('setname/', views.set_full_name),

    # ── Contacts ──────────────────────────────────────────────────────────────
    path('contacts/sync/', views.util_views.send_contacts, name='sync-contacts'),

    # ── Products ──────────────────────────────────────────────────────────────
    # GET  /api/products/          list (supports ?search= and ?category=)
    # GET  /api/products/<id>/     detail
    path('products/', views.products.get_products, name='product-list'),
    path('products/collections/', views.products.get_product_collections, name='product-collections'),
    path('products/featured/', views.products.get_featured_products, name='product-featured'),
    path('products/<int:product_id>/', views.products.get_product_detail, name='product-detail'),
    path('products/<int:product_id>/affiliate-click/', views.products.record_affiliate_click, name='product-affiliate-click'),
    path('products/quiz/', views.products.create_quiz_attempt, name='product-quiz'),

    # ── Event Reminders ──────────────────────────────────────────────────────
    path('reminders/', views.reminders.list_reminders, name='reminder-list'),
    path('reminders/create/', views.reminders.create_reminder, name='reminder-create'),
    path('reminders/upcoming/', views.reminders.upcoming_reminders, name='reminder-upcoming'),
    path('reminders/<int:reminder_id>/', views.reminders.update_delete_reminder, name='reminder-detail'),

    # ── Notification Inbox ───────────────────────────────────────────────────
    path('notifications/', views.notification_views.list_notifications, name='notification-list'),
    path('notifications/<int:notification_id>/read/', views.notification_views.mark_notification_read, name='notification-read'),

    # ── Wishlist ──────────────────────────────────────────────────────────────
    path('wishlist/', views.wishlists.get_wishlist),
    path('wishlist/create/', views.wishlists.create_wishlist, name='wishlist-create'),
    path('wishlist/delete/', views.wishlists.delete_wishlist, name='wishlist-delete'),
    path('wishlist/add_product/', views.wishlists.add_to_wishlist, name='wishlist-add-product'),
    path('wishlist/remove_product/', views.wishlists.remove_from_wishlist, name='wishlist-remove-product'),
    path('wishlist/update_title/', views.wishlists.update_wishlist_title, name='wishlist-update-title'),
    path('wishlist/update_visibility/', views.wishlists.update_wishlist_visibility, name='wishlist-update-visibility'),

    # ── Secret Gift Exchange ──────────────────────────────────────────────────
    # GET  /api/exchange/          my exchanges (list)
    # POST /api/exchange/create/   create new
    # POST /api/exchange/join/     join by invite code
    # GET  /api/exchange/<id>/     detail + my assignment if drawn
    # POST /api/exchange/<id>/draw/
    # GET  /api/exchange/<id>/my/  my assignment only
    path('exchange/', views.gift_exchange.list_exchanges, name='exchange-list'),
    path('exchange/create/', views.gift_exchange.create_exchange, name='exchange-create'),
    path('exchange/join/', views.gift_exchange.join_exchange, name='exchange-join'),
    path('exchange/<int:exchange_id>/', views.gift_exchange.exchange_detail, name='exchange-detail'),
    path('exchange/<int:exchange_id>/accept/', views.gift_exchange.accept_exchange_invitation, name='exchange-accept'),
    path('exchange/<int:exchange_id>/reject/', views.gift_exchange.reject_exchange_invitation, name='exchange-reject'),
    path('exchange/<int:exchange_id>/draw/', views.gift_exchange.draw_assignments, name='exchange-draw'),
    path('exchange/<int:exchange_id>/my/', views.gift_exchange.my_assignment, name='exchange-my-assignment'),

    # ── Qattah (Collaborative Crowdfunding) ───────────────────────────────────
    # GET  /api/qattah/            active Qattahs (?mine=true for own)
    # POST /api/qattah/create/     start a Qattah
    # POST /api/qattah/join/       join by invite code
    # GET  /api/qattah/my-pledges/ all my contributions
    # GET  /api/qattah/<id>/       detail
    # POST /api/qattah/<id>/pledge/ submit a pledge
    path('qattah/', views.qattah.list_qattahs, name='qattah-list'),
    path('qattah/create/', views.qattah.create_qattah, name='qattah-create'),
    path('qattah/join/', views.qattah.join_qattah, name='qattah-join'),
    path('qattah/my-pledges/', views.qattah.my_pledges, name='qattah-my-pledges'),
    path('qattah/<int:qattah_id>/', views.qattah.qattah_detail, name='qattah-detail'),
    path('qattah/<int:qattah_id>/accept/', views.qattah.accept_qattah_invitation, name='qattah-accept'),
    path('qattah/<int:qattah_id>/reject/', views.qattah.reject_qattah_invitation, name='qattah-reject'),
    path('qattah/<int:qattah_id>/pledge/', views.qattah.make_pledge, name='qattah-pledge'),
]
