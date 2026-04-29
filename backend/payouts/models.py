from django.db import models
from django.utils import timezone


class Merchant(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="bank_accounts"
    )
    account_number = models.CharField(max_length=32)
    ifsc = models.CharField(max_length=16)
    bank_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ("CREDIT", "Credit"),
        ("HOLD", "Hold"),
        ("RELEASE", "Release"),
        ("PAYOUT_DEBIT", "Payout Debit"),
    ]

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="ledger_entries"
    )
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    amount_paise = models.BigIntegerField()
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.merchant.name} - {self.entry_type} - {self.amount_paise}"


class Payout(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="payouts"
    )
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE
    )
    amount_paise = models.BigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )
    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout #{self.id} - {self.status}"


class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="idempotency_keys"
    )
    key = models.CharField(max_length=255)
    response_data = models.JSONField(blank=True, null=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("merchant", "key")

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.merchant.name} - {self.key}"