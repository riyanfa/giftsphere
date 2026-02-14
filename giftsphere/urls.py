from django.contrib import admin
from django.urls import path
from core import views
from core.views import get_current_user

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login URLs
    path('api/login/request/', views.request_otp), # Screen 1
    path('api/login/verify/', views.verify_otp),   # Screen 2

    # Data URLs
    path('api/products/', views.get_products),
    path('api/wishlist',views.get_wishlist),

    #Session URL
    path('api/me/', get_current_user),
]