from django.urls import path
from . import views

urlpatterns = [
    # Login URLs - *\
    # Removed 'api/' prefix because giftsphere/urls.py already has it which made it duplicate
    # and caused error during sending post reqs to http://127.0.0.1:8000/api/login/request/ for example
    path('login/request/', views.auth.request_otp),
    path('login/verify/', views.auth.verify_otp),

    # Data URLs - REMOVE 'api/' prefix
    path('products/', views.products.get_products),
    path('wishlist/', views.wishlists.get_wishlist),
    path('wishlist/delete/', views.wishlists.delete_wishlist, name='delete-wishlist'),
    path('setname/',views.set_full_name),
    path('me/', views.get_current_user),
]