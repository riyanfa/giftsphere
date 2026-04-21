from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet

# ── FCM Device router ─────────────────────────────────────────────────────────
# POST   /api/devices/                   register a device token
# GET    /api/devices/                   list the current user's devices
# DELETE /api/devices/{registration_id}/ remove a device (call on logout)
fcm_router = DefaultRouter()
fcm_router.register(r'devices', FCMDeviceAuthorizedViewSet, basename='fcmdevice')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/', include(fcm_router.urls)),

    # ── API Documentation (drf-spectacular) ───────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)