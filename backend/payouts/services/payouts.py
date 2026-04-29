
def trigger_payout(payout_id):
    from payouts.tasks import process_payout  # MOVE INSIDE
    process_payout.delay(payout_id)
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from payouts.models import (
    Merchant,
    BankAccount,
    Payout,
    LedgerEntry,
    IdempotencyKey
)
from payouts.services.ledger import get_available_balance


def create_payout(*, merchant, amount_paise, bank_account_id, idempotency_key):
    with transaction.atomic():

        existing_key = IdempotencyKey.objects.filter(
            merchant=merchant,
            key=idempotency_key,
            expires_at__gt=timezone.now()
        ).first()

        if existing_key:
            return existing_key.response_data

        merchant = Merchant.objects.select_for_update().get(id=merchant.id)

        available_balance = get_available_balance(merchant)

        if available_balance < amount_paise:
            raise ValidationError("Insufficient balance")

        bank_account = BankAccount.objects.get(
            id=bank_account_id,
            merchant=merchant
        )

        payout = Payout.objects.create(
            merchant=merchant,
            bank_account=bank_account,
            amount_paise=amount_paise,
            status="PENDING"
        )

        LedgerEntry.objects.create(
            merchant=merchant,
            entry_type="HOLD",
            amount_paise=amount_paise,
            reference_type="PAYOUT",
            reference_id=str(payout.id)
        )

        response_data = {
            "payout_id": payout.id,
            "status": payout.status,
            "amount_paise": payout.amount_paise
        }

        IdempotencyKey.objects.create(
            merchant=merchant,
            key=idempotency_key,
            response_data=response_data,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # process_payout.delay(payout.id)
        trigger_payout(payout.id)

        return response_data