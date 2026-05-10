from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import GiftAssignment, SecretGiftExchange, SecretGiftParticipant
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
        .filter(
            participant_statuses__user=request.user,
            participant_statuses__status__in=[
                SecretGiftParticipant.STATUS_ACCEPTED,
                SecretGiftParticipant.STATUS_INVITED,
            ],
        )
        .prefetch_related(
            'participants', 'participants__profile',
            'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
        )
        .select_related('organizer', 'organizer__profile')
        .distinct()
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
            .prefetch_related(
                'participants', 'participants__profile',
                'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
            )
            .select_related('organizer', 'organizer__profile')
            .get(id=exchange_id)
        )
    except SecretGiftExchange.DoesNotExist:
        return Response({'error': 'Exchange not found.'}, status=404)

    can_view = (
        exchange.organizer_id == request.user.id
        or SecretGiftParticipant.objects.filter(
            exchange=exchange,
            user=request.user,
            status__in=[SecretGiftParticipant.STATUS_ACCEPTED, SecretGiftParticipant.STATUS_INVITED],
        ).exists()
    )
    if not can_view:
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
        SecretGiftParticipant.objects.create(
            exchange=exchange,
            user=request.user,
            status=SecretGiftParticipant.STATUS_ACCEPTED,
        )
        return Response(SecretGiftExchangeSerializer(exchange).data)

    return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_exchange(request):
    invite_code = str(request.data.get('invite_code', '')).strip()

    if not invite_code:
        return Response({'error': 'invite_code is required.'}, status=400)

    try:
        exchange = (
            SecretGiftExchange.objects
            .prefetch_related(
                'participants', 'participants__profile',
                'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
            )
            .select_related('organizer', 'organizer__profile')
            .get(invite_code=invite_code)
        )
    except SecretGiftExchange.DoesNotExist:
        return Response({'error': 'Invalid invite code.'}, status=404)

    if exchange.status == 'COMPLETED':
        return Response({'error': 'This exchange is closed.'}, status=400)

    participant, created = SecretGiftParticipant.objects.get_or_create(
        exchange=exchange,
        user=request.user,
        defaults={'status': SecretGiftParticipant.STATUS_ACCEPTED},
    )

    if not created and participant.status == SecretGiftParticipant.STATUS_ACCEPTED:
        return Response(
            {
                'message': 'You already joined this exchange.',
                'exchange': SecretGiftExchangeSerializer(exchange).data,
            }
        )

    if not created:
        participant.status = SecretGiftParticipant.STATUS_ACCEPTED
        participant.save(update_fields=['status', 'updated_at'])

    exchange.refresh_from_db()

    return Response(
        {
            'message': 'Joined successfully.',
            'exchange': SecretGiftExchangeSerializer(exchange).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_exchange_invitation(request, exchange_id):
    try:
        participant = SecretGiftParticipant.objects.select_related('exchange').get(
            exchange_id=exchange_id,
            user=request.user,
        )
    except SecretGiftParticipant.DoesNotExist:
        return Response({'error': 'Exchange invitation not found.'}, status=404)

    if participant.exchange.status == 'COMPLETED':
        return Response({'error': 'This exchange is closed.'}, status=400)

    participant.status = SecretGiftParticipant.STATUS_ACCEPTED
    participant.save(update_fields=['status', 'updated_at'])
    return Response(
        {
            'message': 'Exchange invitation accepted.',
            'exchange': SecretGiftExchangeSerializer(participant.exchange).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_exchange_invitation(request, exchange_id):
    try:
        participant = SecretGiftParticipant.objects.select_related('exchange').get(
            exchange_id=exchange_id,
            user=request.user,
        )
    except SecretGiftParticipant.DoesNotExist:
        return Response({'error': 'Exchange invitation not found.'}, status=404)

    participant.status = SecretGiftParticipant.STATUS_REJECTED
    participant.save(update_fields=['status', 'updated_at'])
    return Response(
        {
            'message': 'Exchange invitation rejected.',
            'exchange': SecretGiftExchangeSerializer(participant.exchange).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_exchange(request, exchange_id):
    try:
        participant = (
            SecretGiftParticipant.objects
            .select_related('exchange')
            .get(exchange_id=exchange_id, user=request.user)
        )
    except SecretGiftParticipant.DoesNotExist:
        return Response({'error': 'Exchange participation not found.'}, status=404)

    exchange = participant.exchange

    if exchange.organizer_id == request.user.id:
        return Response({'error': 'Organizer cannot leave their own exchange.'}, status=400)

    if exchange.status != 'PENDING':
        return Response({'error': 'You cannot leave after assignments have been drawn.'}, status=400)

    if participant.status == SecretGiftParticipant.STATUS_LEFT:
        return Response(
            {
                'message': 'You already left this exchange.',
                'exchange': SecretGiftExchangeSerializer(exchange).data,
            }
        )

    participant.status = SecretGiftParticipant.STATUS_LEFT
    participant.save(update_fields=['status', 'updated_at'])

    return Response(
        {
            'message': 'Left exchange successfully.',
            'exchange': SecretGiftExchangeSerializer(exchange).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def draw_assignments(request, exchange_id):
    try:
        with transaction.atomic():
            exchange = SecretGiftExchange.objects.select_for_update().get(id=exchange_id)

            if exchange.organizer != request.user:
                return Response({"error": "Only organizer can draw"}, status=403)

            participants = list(
                SecretGiftParticipant.objects
                .filter(exchange=exchange, status=SecretGiftParticipant.STATUS_ACCEPTED)
                .select_related('user')
                .order_by('id')
            )
            users = [participant.user for participant in participants]

            if len(users) < 2:
                return Response({"error": "Not enough accepted participants"}, status=400)

            receivers = users.copy()
            random.shuffle(receivers)
            if any(giver.id == receiver.id for giver, receiver in zip(users, receivers)):
                receivers = users[1:] + users[:1]

            GiftAssignment.objects.filter(exchange=exchange).delete()

            for giver, receiver in zip(users, receivers):
                GiftAssignment.objects.create(
                    exchange=exchange,
                    giver=giver,
                    receiver=receiver,
                )

            exchange.status = 'ACTIVE'
            exchange.draw_date = timezone.now()
            exchange.save(update_fields=['status', 'draw_date'])
    except SecretGiftExchange.DoesNotExist:
        return Response({"error": "Exchange not found"}, status=404)

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
