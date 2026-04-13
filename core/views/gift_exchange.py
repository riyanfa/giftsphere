from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User

from ..models import SecretGiftExchange, GiftAssignment
from ..serializers import SecretGiftExchangeSerializer, GiftAssignmentSerializer

import random


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_exchange(request):
    serializer = SecretGiftExchangeSerializer(data=request.data)

    if serializer.is_valid():
        exchange = serializer.save(organizer=request.user)
        exchange.participants.add(request.user)  # organizer joins automatically
        return Response(serializer.data)

    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_exchange(request, exchange_id):
    try:
        exchange = SecretGiftExchange.objects.get(id=exchange_id)
    except SecretGiftExchange.DoesNotExist:
        return Response({"error": "Exchange not found"}, status=404)

    exchange.participants.add(request.user)
    return Response({"message": "Joined successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def draw_assignments(request, exchange_id):
    try:
        exchange = SecretGiftExchange.objects.get(id=exchange_id)
    except SecretGiftExchange.DoesNotExist:
        return Response({"error": "Exchange not found"}, status=404)

    if exchange.organizer != request.user:
        return Response({"error": "Only organizer can draw"}, status=403)

    participants = list(exchange.participants.all())

    if len(participants) < 2:
        return Response({"error": "Not enough participants"}, status=400)

    receivers = participants.copy()
    random.shuffle(receivers)

    # Ensure no one gets themselves
    for i in range(len(participants)):
        if participants[i] == receivers[i]:
            receivers[i], receivers[(i+1) % len(receivers)] = receivers[(i+1) % len(receivers)], receivers[i]

    # Clear old assignments
    GiftAssignment.objects.filter(exchange=exchange).delete()

    # Create new assignments
    for giver, receiver in zip(participants, receivers):
        GiftAssignment.objects.create(
            exchange=exchange,
            giver=giver,
            receiver=receiver
        )

    exchange.status = 'ACTIVE'
    exchange.save()

    return Response({"message": "Assignments generated"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_assignment(request, exchange_id):
    try:
        assignment = GiftAssignment.objects.get(exchange_id=exchange_id, giver=request.user)
    except GiftAssignment.DoesNotExist:
        return Response({"error": "Assignment not found"}, status=404)

    serializer = GiftAssignmentSerializer(assignment)
    return Response(serializer.data)