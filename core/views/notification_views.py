from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import InAppNotification
from ..serializers import InAppNotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_notifications(request):
    notifications = InAppNotification.objects.filter(user=request.user).order_by('-created_at')
    serializer = InAppNotificationSerializer(notifications, many=True)
    unread_count = InAppNotification.objects.filter(user=request.user, is_read=False).count()
    return Response({
        'unread_count': unread_count,
        'notifications': serializer.data,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    try:
        notification = InAppNotification.objects.get(id=notification_id, user=request.user)
    except InAppNotification.DoesNotExist:
        return Response({'error': 'Notification not found.'}, status=404)

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])

    serializer = InAppNotificationSerializer(notification)
    return Response(serializer.data)
