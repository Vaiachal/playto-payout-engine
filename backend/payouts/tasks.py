import random
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from payouts.models import Payout, LedgerEntry


@shared_task
def process_payout(payout_id):
    payout = Payout.objects.get(id=payout_id)

    if payout.status != "PENDING":
        return

    payout.status = "PROCESSING"
    payout.save()

    outcome = random.choices(
        ["COMPLETED", "FAILED", "STUCK"],
        weights=[70, 20, 10]
    )[0]

    if outcome == "STUCK":
        payout.next_retry_at = timezone.now() + timedelta(seconds=30)
        payout.save()
        return

    with transaction.atomic():
        payout.refresh_from_db()

        if outcome == "COMPLETED":
            payout.status = "COMPLETED"
            payout.save()

            LedgerEntry.objects.create(
                merchant=payout.merchant,
                entry_type="PAYOUT_DEBIT",
                amount_paise=payout.amount_paise,
                reference_type="PAYOUT",
                reference_id=str(payout.id)
            )

        elif outcome == "FAILED":
            payout.status = "FAILED"
            payout.save()

            LedgerEntry.objects.create(
                merchant=payout.merchant,
                entry_type="RELEASE",
                amount_paise=payout.amount_paise,
                reference_type="PAYOUT",
                reference_id=str(payout.id)
            )


@shared_task
def retry_stuck_payouts():
    stuck_payouts = Payout.objects.filter(
        status="PROCESSING",
        next_retry_at__lte=timezone.now()
    )

    for payout in stuck_payouts:
        if payout.attempt_count >= 3:
            with transaction.atomic():
                payout.status = "FAILED"
                payout.save()

                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    entry_type="RELEASE",
                    amount_paise=payout.amount_paise,
                    reference_type="PAYOUT",
                    reference_id=str(payout.id)
                )
            continue

        payout.attempt_count += 1
        payout.next_retry_at = timezone.now() + timedelta(
            seconds=30 * (2 ** payout.attempt_count)
        )
        payout.status = "PENDING"
        payout.save()

        process_payout.delay(payout.id)