from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from payouts.serializers import PayoutRequestSerializer
from payouts.services.payouts import create_payout
from payouts.services.ledger import get_available_balance
from payouts.models import Merchant, Payout, LedgerEntry
from payouts.tasks import process_payout


class RetryPayoutAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request, payout_id):
        try:
            payout = Payout.objects.get(id=payout_id)
        except Payout.DoesNotExist:
            return Response({"error": "Payout not found"}, status=404)

        if payout.status != "FAILED":
            return Response(
                {"error": "Only failed payouts can be retried"},
                status=400
            )

        payout.status = "PENDING"
        payout.save()

        process_payout.delay(payout.id)

        return Response({"message": "Retry initiated"})


class PayoutCreateAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"error": "Missing Idempotency-Key header"},
                status=400
            )

        merchant = Merchant.objects.first()

        result = create_payout(
            merchant=merchant,
            amount_paise=serializer.validated_data["amount_paise"],
            bank_account_id=serializer.validated_data["bank_account_id"],
            idempotency_key=idempotency_key
        )

        return Response(result)


class BalanceAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        merchant = Merchant.objects.first()

        held_balance = LedgerEntry.objects.filter(
            merchant=merchant,
            entry_type="HOLD"
        ).aggregate(total=models.Sum("amount_paise"))["total"] or 0

        return Response({
            "available_balance": get_available_balance(merchant),
            "held_balance": held_balance
        })


class PayoutListAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        merchant = Merchant.objects.first()

        payouts = Payout.objects.filter(
            merchant=merchant
        ).order_by("-created_at").values()

        return Response(list(payouts))


class PayoutDetailAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, payout_id):
        merchant = Merchant.objects.first()

        payout = Payout.objects.get(
            id=payout_id,
            merchant=merchant
        )

        return Response({
            "id": payout.id,
            "status": payout.status,
            "amount_paise": payout.amount_paise,
            "attempt_count": payout.attempt_count,
            "created_at": payout.created_at
        })