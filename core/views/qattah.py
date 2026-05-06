from decimal import Decimal

from django.db import transaction, IntegrityError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import GroupGift, GroupGiftParticipant, Pledge, Product
from ..serializers import GroupGiftSerializer, PledgeSerializer
from ..notifications import notify_pledge_received, notify_qattah_completed


# ---------------------------------------------------------------------------
# 1. CREATE a Qattah
#    POST /qattah/create/
#    Body: { "title": "...", "product_id": 3 }
#    target_amount is automatically pulled from the product price.
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_qattah(request):
    """
    Start a new Qattah. The target_amount is locked to the product's price
    so it cannot be manually manipulated by the client.
    """
    product_id = request.data.get('product_id')
    title = request.data.get('title', '').strip()
    payment_method_note = request.data.get('payment_method_note', '').strip()

    if not product_id:
        return Response({'error': 'product_id is required.'}, status=400)

    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found.'}, status=404)

    if not title:
        title = f"Qattah for {product.name}"

    group_gift = GroupGift.objects.create(
        organizer=request.user,
        product=product,
        title=title,
        target_amount=product.price,   # Auto-set from product price
        collected_amount=Decimal('0.00'),
        payment_method_note=payment_method_note,
        status='ACTIVE',
    )
    GroupGiftParticipant.objects.create(
        group_gift=group_gift,
        user=request.user,
        status=GroupGiftParticipant.STATUS_ACCEPTED,
    )

    serializer = GroupGiftSerializer(group_gift, context={'request': request})
    return Response(serializer.data, status=201)


# ---------------------------------------------------------------------------
# 2. LIST Qattahs
#    GET /qattah/              → all ACTIVE Qattahs (public feed)
#    GET /qattah/?mine=true    → only Qattahs I organize
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_qattahs(request):
    mine = request.query_params.get('mine', 'false').lower() == 'true'

    if mine:
        qs = GroupGift.objects.filter(organizer=request.user)
    else:
        qs = GroupGift.objects.filter(status='ACTIVE')

    qs = (
        qs.select_related('organizer', 'organizer__profile', 'recipient', 'recipient__profile', 'product')
        .prefetch_related(
            'participants', 'participants__profile',
            'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
            'pledges', 'pledges__user', 'pledges__user__profile',
        )
        .order_by('-created_at')
    )

    serializer = GroupGiftSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# 3. DETAIL — single Qattah with all pledges
#    GET /qattah/<id>/
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def qattah_detail(request, qattah_id):
    try:
        group_gift = (
            GroupGift.objects
            .select_related('organizer', 'organizer__profile', 'recipient', 'recipient__profile', 'product')
            .prefetch_related(
                'participants', 'participants__profile',
                'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
                'pledges', 'pledges__user', 'pledges__user__profile',
            )
            .get(id=qattah_id)
        )
    except GroupGift.DoesNotExist:
        return Response({'error': 'Qattah not found.'}, status=404)

    serializer = GroupGiftSerializer(group_gift, context={'request': request})
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# 4. JOIN — join a Qattah using invite code
#    POST /qattah/join/
#    Body: { "invite_code": "12345678" }
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_qattah(request):
    invite_code = str(request.data.get('invite_code', '')).strip()

    if not invite_code:
        return Response({'error': 'invite_code is required.'}, status=400)

    try:
        group_gift = (
            GroupGift.objects
            .select_related('organizer', 'organizer__profile', 'recipient', 'recipient__profile', 'product')
            .prefetch_related(
                'participants', 'participants__profile',
                'participant_statuses', 'participant_statuses__user', 'participant_statuses__user__profile',
                'pledges', 'pledges__user', 'pledges__user__profile',
            )
            .get(invite_code=invite_code)
        )
    except GroupGift.DoesNotExist:
        return Response({'error': 'Invalid invite code.'}, status=404)

    if group_gift.status != 'ACTIVE':
        return Response({'error': 'This Qattah is not open for joining.'}, status=400)

    participant, created = GroupGiftParticipant.objects.get_or_create(
        group_gift=group_gift,
        user=request.user,
        defaults={'status': GroupGiftParticipant.STATUS_ACCEPTED},
    )

    if not created and participant.status == GroupGiftParticipant.STATUS_ACCEPTED:
        return Response(
            {
                'message': 'You already joined this Qattah.',
                'qattah': GroupGiftSerializer(group_gift, context={'request': request}).data,
            }
        )

    if not created:
        participant.status = GroupGiftParticipant.STATUS_ACCEPTED
        participant.save(update_fields=['status', 'updated_at'])

    group_gift.refresh_from_db()

    return Response(
        {
            'message': 'Joined successfully.',
            'qattah': GroupGiftSerializer(group_gift, context={'request': request}).data,
        },
        status=200,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_qattah_invitation(request, qattah_id):
    try:
        participant = GroupGiftParticipant.objects.select_related('group_gift').get(
            group_gift_id=qattah_id,
            user=request.user,
        )
    except GroupGiftParticipant.DoesNotExist:
        return Response({'error': 'Qattah invitation not found.'}, status=404)

    if participant.group_gift.status != 'ACTIVE':
        return Response({'error': 'This Qattah is not open for joining.'}, status=400)

    participant.status = GroupGiftParticipant.STATUS_ACCEPTED
    participant.save(update_fields=['status', 'updated_at'])
    return Response(
        {
            'message': 'Qattah invitation accepted.',
            'qattah': GroupGiftSerializer(participant.group_gift, context={'request': request}).data,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_qattah_invitation(request, qattah_id):
    try:
        participant = GroupGiftParticipant.objects.select_related('group_gift').get(
            group_gift_id=qattah_id,
            user=request.user,
        )
    except GroupGiftParticipant.DoesNotExist:
        return Response({'error': 'Qattah invitation not found.'}, status=404)

    participant.status = GroupGiftParticipant.STATUS_REJECTED
    participant.save(update_fields=['status', 'updated_at'])
    return Response(
        {
            'message': 'Qattah invitation rejected.',
            'qattah': GroupGiftSerializer(participant.group_gift, context={'request': request}).data,
        }
    )


# ---------------------------------------------------------------------------
# 5. PLEDGE — contribute to a Qattah
#    POST /qattah/<id>/pledge/
#    Body: { "amount": "50.00", "message": "Happy Birthday!" }
#
#    Rules enforced:
#      • Qattah must be ACTIVE.
#      • Amount must be > 0.
#      • Amount cannot exceed the remaining balance (smart validation).
#      • When collected_amount == target_amount the status flips to COMPLETED.
# ---------------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_pledge(request, qattah_id):
    """
    Submit a pledge for a Qattah.
    Rules:
      • Qattah must be ACTIVE.
      • Amount must be > 0 and ≤ remaining balance.
      • One pledge per user per Qattah (duplicate returns 409).
      • Auto-completes the Qattah when the goal is reached.
    """
    # Validate amount before touching the DB
    try:
        amount = Decimal(str(request.data.get('amount', '0')))
    except Exception:
        return Response({'error': 'Invalid amount.'}, status=400)

    if amount <= 0:
        return Response({'error': 'Amount must be greater than zero.'}, status=400)

    try:
        with transaction.atomic():
            # Lock the row so concurrent pledges don't race
            group_gift = GroupGift.objects.select_for_update().get(id=qattah_id)

            if group_gift.status != 'ACTIVE':
                return Response({'error': 'This Qattah is already completed.'}, status=400)

            is_accepted_participant = GroupGiftParticipant.objects.filter(
                group_gift=group_gift,
                user=request.user,
                status=GroupGiftParticipant.STATUS_ACCEPTED,
            ).exists()
            if not is_accepted_participant:
                return Response({'error': 'You must join this Qattah before pledging.'}, status=403)

            if Pledge.objects.filter(group_gift=group_gift, user=request.user).exists():
                return Response(
                    {'error': 'You have already pledged to this Qattah.'},
                    status=409,
                )

            remaining = group_gift.target_amount - group_gift.collected_amount
            if amount > remaining:
                return Response(
                    {
                        'error': 'Amount exceeds the remaining balance.',
                        'remaining_amount': str(remaining),
                    },
                    status=400,
                )

            message = request.data.get('message', '')
            pledge_status = request.data.get('status', Pledge.STATUS_PLEDGED)
            if pledge_status not in {Pledge.STATUS_PLEDGED, Pledge.STATUS_PAID_EXTERNALLY}:
                return Response({'error': 'Invalid pledge status.'}, status=400)

            pledge = Pledge.objects.create(
                group_gift=group_gift,
                user=request.user,
                amount=amount,
                status=pledge_status,
                message=message,
            )

            group_gift.collected_amount += amount

            # Auto-complete when the goal is exactly reached
            if group_gift.collected_amount >= group_gift.target_amount:
                group_gift.collected_amount = group_gift.target_amount  # prevent float drift
                group_gift.status = 'COMPLETED'

            group_gift.save()

    except GroupGift.DoesNotExist:
        return Response({'error': 'Qattah not found.'}, status=404)
    except IntegrityError:
        # unique_together ('group_gift', 'user') was violated
        return Response(
            {'error': 'You have already pledged to this Qattah.'},
            status=409,
        )

    serializer = GroupGiftSerializer(group_gift, context={'request': request})

    # ── Fire notifications AFTER the transaction has committed ────────────────
    just_completed = group_gift.status == 'COMPLETED'
    if just_completed:
        notify_qattah_completed(group_gift)        # → all pledgers + organizer
    else:
        notify_pledge_received(group_gift, pledge)  # → organizer only
    # ─────────────────────────────────────────────────────────────────────────

    return Response(
        {
            'message': 'Pledge submitted successfully!',
            'qattah': serializer.data,
            'pledge': PledgeSerializer(pledge).data,
        },
        status=201,
    )


# ---------------------------------------------------------------------------
# 6. MY PLEDGES — all pledges the current user has made
#    GET /qattah/my-pledges/
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_pledges(request):
    """
    All pledges the current user has made.
    """
    pledges = (
        Pledge.objects
        .filter(user=request.user)
        .select_related('group_gift', 'group_gift__product', 'user', 'user__profile')
        .order_by('-timestamp')
    )

    data = [
        {
            'pledge_id': p.id,
            'amount': str(p.amount),
            'status': p.status,
            'message': p.message,
            'timestamp': p.timestamp,
            'qattah': {
                'id': p.group_gift.id,
                'title': p.group_gift.title,
                'status': p.group_gift.status,
                'product_name': p.group_gift.product.name,
                'product_image': p.group_gift.product.image_url,
                'affiliate_link': p.group_gift.product.affiliate_link,
            },
        }
        for p in pledges
    ]

    return Response(data)
