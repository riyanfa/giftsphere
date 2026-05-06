from fcm_django.models import FCMDevice
from django.contrib.auth.models import User
from firebase_admin.messaging import Message, Notification as FCMNotification

from .models import InAppNotification


def _normalise_user_pks(users):
    if isinstance(users, User):
        return [users.pk]

    user_pks = []
    for user in users:
        user_pks.append(user.pk if isinstance(user, User) else user)

    return list(dict.fromkeys(user_pks))


def _create_inbox_records(user_pks, title: str, body: str, data: dict = None):
    try:
        payload = data or {}
        notification_type = str(payload.get('type', ''))
        InAppNotification.objects.bulk_create([
            InAppNotification(
                user_id=user_pk,
                title=title,
                body=body,
                notification_type=notification_type,
                data={k: str(v) for k, v in payload.items()},
            )
            for user_pk in user_pks
        ])
    except Exception:
        # Notification storage should not crash the main request.
        pass


def _send(users, title: str, body: str, data: dict = None):
    """
    Internal helper — sends a push notification to all active devices
    belonging to the given users (queryset, list, or single User instance).
    Silently no-ops if Firebase isn't initialised or no devices are found.
    """
    try:
        user_pks = _normalise_user_pks(users)
        if not user_pks:
            return

        _create_inbox_records(user_pks, title, body, data)

        devices = FCMDevice.objects.filter(user_id__in=user_pks, active=True)
        if not devices.exists():
            return

        message = Message(
            notification=FCMNotification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
        )
        devices.send_message(message)

    except Exception:
        # Never let a notification failure crash the main request.
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Qattah (GroupGift) notifications
# ─────────────────────────────────────────────────────────────────────────────

def notify_pledge_received(group_gift, pledge):
    """Notifies the Qattah organizer that a new pledge has been made."""
    pledger_name = pledge.user.first_name or pledge.user.username
    _send(
        users=group_gift.organizer,
        title="New pledge on your Qattah! 🎉",
        body=f"{pledger_name} contributed {pledge.amount} SAR to \"{group_gift.title}\"",
        data={"type": "PLEDGE_RECEIVED", "qattah_id": str(group_gift.id)},
    )


def notify_qattah_completed(group_gift):
    """Notifies all pledgers + the organizer that the Qattah goal is reached."""
    pledger_ids = list(
        group_gift.pledges.values_list('user_id', flat=True).distinct()
    )
    recipient_ids = list(set(pledger_ids + [group_gift.organizer_id]))

    _send(
        users=recipient_ids,
        title="Qattah Complete! 🛍️",
        body=f"\"{group_gift.title}\" reached its goal! Time to buy the gift.",
        data={"type": "QATTAH_COMPLETED", "qattah_id": str(group_gift.id)},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Secret Gift Exchange notifications
# ─────────────────────────────────────────────────────────────────────────────

def notify_draw_completed(exchange):
    """Notifies all participants that the Secret Gift draw has been done."""
    try:
        participant_ids = list(
            exchange.participant_statuses
            .filter(status='ACCEPTED')
            .values_list('user_id', flat=True)
        )
    except Exception:
        participant_ids = list(
            exchange.participants.values_list('id', flat=True)
        )

    _send(
        users=participant_ids,
        title="The draw is done! 🎁",
        body=f"Check who you're buying for in \"{exchange.title}\"",
        data={"type": "DRAW_COMPLETED", "exchange_id": str(exchange.id)},
    )
