from django.test import TransactionTestCase
from concurrent.futures import ThreadPoolExecutor

from payouts.models import Merchant, BankAccount, LedgerEntry
from payouts.services.payouts import create_payout


class PayoutConcurrencyTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(
            name="Test Merchant",
            email="test@example.com"
        )

        self.bank_account = BankAccount.objects.create(
            merchant=self.merchant,
            account_number="1234567890",
            ifsc="HDFC0001",
            bank_name="HDFC"
        )

        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type="CREDIT",
            amount_paise=10000
        )

    def attempt_payout(self):
        try:
            create_payout(
                merchant=self.merchant,
                amount_paise=6000,
                bank_account_id=self.bank_account.id,
                idempotency_key=str(id(self))
            )
            return True
        except Exception:
            return False

    def test_only_one_concurrent_payout_succeeds(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: self.attempt_payout(), range(2)))

        assert sum(results) == 1


class IdempotencyTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(
            name="Idempotency Merchant",
            email="idem@example.com"
        )

        self.bank_account = BankAccount.objects.create(
            merchant=self.merchant,
            account_number="9999999999",
            ifsc="ICIC0001",
            bank_name="ICICI"
        )

        LedgerEntry.objects.create(
            merchant=self.merchant,
            entry_type="CREDIT",
            amount_paise=50000
        )

    def test_same_idempotency_key_returns_same_payout(self):
        key = "same-key-123"

        first = create_payout(
            merchant=self.merchant,
            amount_paise=10000,
            bank_account_id=self.bank_account.id,
            idempotency_key=key
        )

        second = create_payout(
            merchant=self.merchant,
            amount_paise=10000,
            bank_account_id=self.bank_account.id,
            idempotency_key=key
        )

        assert first == second