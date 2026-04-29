from django.core.management.base import BaseCommand
from payouts.models import Merchant, BankAccount, LedgerEntry


class Command(BaseCommand):
    help = "Seed test merchants and balances"

    def handle(self, *args, **kwargs):
        Merchant.objects.all().delete()

        merchant1 = Merchant.objects.create(
            name="Acme Agency",
            email="acme@example.com"
        )

        merchant2 = Merchant.objects.create(
            name="Growth Labs",
            email="growth@example.com"
        )

        BankAccount.objects.create(
            merchant=merchant1,
            account_number="111122223333",
            ifsc="HDFC0001234",
            bank_name="HDFC Bank"
        )

        BankAccount.objects.create(
            merchant=merchant2,
            account_number="444455556666",
            ifsc="ICIC0005678",
            bank_name="ICICI Bank"
        )

        LedgerEntry.objects.create(
            merchant=merchant1,
            entry_type="CREDIT",
            amount_paise=100000
        )

        LedgerEntry.objects.create(
            merchant=merchant2,
            entry_type="CREDIT",
            amount_paise=250000
        )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully"))