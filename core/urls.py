from django.urls import path

from . import views
urlpatterns = [
    # Login URLs
    path('api/login/request/',views.auth.request_otp), # Screen 1
    path('api/login/verify/',views.auth.verify_otp ),   # Screen 2

    # Data URLs
    path('api/products/', views.products.get_products),
    path('api/wishlist/',views.wishlists.get_wishlist),
    path('api/wishlist/delete/',views.wishlists.delete_wishlist,name='delete-wishlist'),
]