from django.urls import path
from . import views


urlpatterns = [
    #Authentication
    path('login/request/', views.auth.request_otp),
    path('login/verify/', views.auth.verify_otp),
    #Products
    path('products/', views.products.get_products),
    #Wishlist
    path('wishlist/', views.wishlists.get_wishlist),
    path('wishlist/delete/', views.wishlists.delete_wishlist, name='delete-wishlist'),
    path('wishlist/create/', views.wishlists.create_wishlist, name='create-wishlist'),
    path('wishlist/add_product/', views.wishlists.add_to_wishlist, name='add_product'),
    path('wishlist/remove_product/', views.wishlists.remove_from_wishlist, name='remove_product'),
    path('wishlist/update_title/', views.wishlists.update_wishlist_title, name='update_title'),
    path('wishlist/update_visibility/', views.wishlists.update_wishlist_visibility, name='update_visibility'),
    #gift exchange
# gift exchange
path('exchange/create/', views.gift_exchange.create_exchange),
path('exchange/<int:exchange_id>/join/', views.gift_exchange.join_exchange),
path('exchange/<int:exchange_id>/draw/', views.gift_exchange.draw_assignments),
path('exchange/<int:exchange_id>/my/', views.gift_exchange.my_assignment),


    path('setname/', views.set_full_name),
    path('profile/me/', views.get_current_user),
    path('contacts/sync/', views.util_views.send_contacts, name='sync-contacts'),
]