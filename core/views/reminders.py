from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import EventReminder
from ..serializers import EventReminderSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reminders(request):
    reminders = (
        EventReminder.objects
        .filter(user=request.user)
        .order_by('event_date')
    )
    serializer = EventReminderSerializer(reminders, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_reminder(request):
    serializer = EventReminderSerializer(data=request.data)
    if serializer.is_valid():
        reminder = serializer.save(user=request.user)
        return Response(EventReminderSerializer(reminder).data, status=201)

    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_reminders(request):
    reminders = (
        EventReminder.objects
        .filter(user=request.user, reminder_date__gte=timezone.now())
        .order_by('reminder_date')[:10]
    )
    serializer = EventReminderSerializer(reminders, many=True)
    return Response(serializer.data)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_delete_reminder(request, reminder_id):
    try:
        reminder = EventReminder.objects.get(id=reminder_id, user=request.user)
    except EventReminder.DoesNotExist:
        return Response({'error': 'Reminder not found.'}, status=404)

    if request.method == 'DELETE':
        reminder.delete()
        return Response(status=204)

    serializer = EventReminderSerializer(reminder, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)
