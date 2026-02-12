from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login URLs
    path('api/login/request/', views.request_otp), # Screen 1
    path('api/login/verify/', views.verify_otp),   # Screen 2

    # Data URLs
    path('api/products/', views.get_products),
]