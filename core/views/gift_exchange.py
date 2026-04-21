from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import SecretGiftExchange, GiftAssignment
from ..serializers import SecretGiftExchangeSerializer, GiftAssignmentSerializer
from ..notifications import notify_draw_completed

import random


# ---------------------------------------------------------------------------
# LIST — all exchanges the current user is part of
#   GET /exchange/
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_exchanges(request):
    """
    Returns every SecretGiftExchange where the current user is a participant
    (including ones they organised), ordered newest first.
    """
    exchanges = (
        SecretGiftExchange.objects
        .filter(participants=request.user)
        .prefetch_related('participants', 'participants__profile')
        .select_related('organizer', 'organizer__profile')
        .order_by('-created_at')
    )
    serializer = SecretGiftExchangeSerializer(exchanges, many=True)
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# DETAIL — single exchange with full participant list and assignments
#   GET /exchange/<id>/
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exchange_detail(request, exchange_id):
    """
    Returns full exchange info. Only participants can view.
    If the draw has been done, also returns the current user's assignment.
    """
    try:
        exchange = (
            SecretGiftExchange.objects
            .prefetch_related('participants', 'participants__profile')
            .select_related('organizer', 'organizer__profile')
            .get(id=exchange_id)
        )
    except SecretGiftExchange.DoesNotExist:
        return Response({'error': 'Exchange not found.'}, status=404)

    if not exchange.participants.filter(id=request.user.id).exists():
        return Response({'error': 'You are not a participant in this exchange.'}, status=403)

    data = SecretGiftExchangeSerializer(exchange).data

    # Attach the current user's assignment if the draw has been done
    try:
        assignment = GiftAssignment.objects.select_related(
            'receiver', 'receiver__profile'
        ).get(exchange=exchange, giver=request.user)
        data['my_assignment'] = GiftAssignmentSerializer(assignment).data
    except GiftAssignment.DoesNotExist:
        data['my_assignment'] = None

    return Response(data)


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

    # Notify all participants that the draw is done
    notify_draw_completed(exchange)

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