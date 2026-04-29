from django.urls import path
from .views import (
    PayoutCreateAPI,
    BalanceAPI,
    PayoutListAPI,
    PayoutDetailAPI,
    RetryPayoutAPI
)

urlpatterns = [
    path("payouts", PayoutCreateAPI.as_view()),
    path("balance", BalanceAPI.as_view()),
    path("payouts/list", PayoutListAPI.as_view()),
    path("payouts/<int:payout_id>", PayoutDetailAPI.as_view()),
    path("payouts/<int:payout_id>/retry", RetryPayoutAPI.as_view()),
]