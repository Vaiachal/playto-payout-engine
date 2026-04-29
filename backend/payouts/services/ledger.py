from django.db.models import Sum, Q
from payouts.models import LedgerEntry


def get_available_balance(merchant):
    credits = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type__in=["CREDIT", "RELEASE"]
    ).aggregate(total=Sum("amount_paise"))["total"] or 0

    debits = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type__in=["HOLD", "PAYOUT_DEBIT"]
    ).aggregate(total=Sum("amount_paise"))["total"] or 0

    return credits - debits


def get_held_balance(merchant):
    holds = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type="HOLD"
    ).aggregate(total=Sum("amount_paise"))["total"] or 0

    releases = LedgerEntry.objects.filter(
        merchant=merchant,
        entry_type="RELEASE"
    ).aggregate(total=Sum("amount_paise"))["total"] or 0

    return holds - releases