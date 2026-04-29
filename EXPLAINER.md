# EXPLAINER.md

## 1. The Ledger

### Balance Calculation Query

```python
LedgerEntry.objects.filter(
    merchant=merchant
).aggregate(
    total=models.Sum(
        Case(
            When(entry_type__in=["CREDIT", "RELEASE"], then=F("amount_paise")),
            When(entry_type__in=["HOLD", "PAYOUT_DEBIT"], then=-F("amount_paise")),
            output_field=BigIntegerField()
        )
    )
)["total"] or 0


Why This Model

I modeled balance as an append-only ledger instead of a mutable balance field because:

It preserves full audit history of all money movements.
It avoids balance drift caused by partial updates.
It allows balance to be derived deterministically from credits/debits.
This mirrors real-world payment ledger systems.

Ledger entries used:

CREDIT → Incoming merchant funds
HOLD → Funds reserved for payout
RELEASE → Held funds returned after failure
PAYOUT_DEBIT → Final debit after payout completion
2. The Lock
Concurrency Protection Code
merchant = Merchant.objects.select_for_update().get(id=merchant.id)
Why This Prevents Overdrafts

This uses a database row lock (SELECT ... FOR UPDATE) inside a transaction.

Effect:

If two payout requests arrive simultaneously:
First transaction locks merchant row.
Second waits until first commits/rolls back.
Prevents race condition where both requests read same balance.

This ensures:

Two simultaneous ₹60 payouts against ₹100 balance
→ Only one succeeds.

3. The Idempotency
How Duplicate Requests Are Detected

Idempotency keys are stored in:

IdempotencyKey

with unique constraint:

unique_together = ("merchant", "key")
Flow

On payout request:

Check if unexpired key exists for merchant
If yes → return stored response
If no → process payout normally
Persist response against key for 24 hours
In-Flight Duplicate Handling

Because idempotency check + creation happen inside the same DB transaction:

Concurrent duplicate requests serialize safely
Unique constraint prevents duplicate inserts
4. The Payout Lifecycle / State Handling
Supported States
PENDING
PROCESSING
COMPLETED
FAILED
Lifecycle

Valid flow:

PENDING → PROCESSING → COMPLETED
PENDING → PROCESSING → FAILED
Retry Flow

If payout gets stuck:

PROCESSING (30s timeout)
→ retry with exponential backoff
→ max 3 attempts
→ FAILED + funds released
Atomic Failure Handling

On payout failure:

with transaction.atomic():
    payout.status = "FAILED"
    payout.save()

    LedgerEntry.objects.create(
        entry_type="RELEASE",
        ...
    )

This guarantees funds release and failure state update happen atomically.

5. The AI Audit
Incorrect AI Suggestion

AI initially suggested:

available_balance = get_available_balance(merchant)

if available_balance < amount:
    raise ValidationError()

# then create payout

without locking.

Why It Was Wrong

This introduced a race condition:

Two concurrent requests could both read same balance
Both could pass validation
Both could create payouts
Merchant overdrafts
Fix Applied

Wrapped in transaction + row lock:

with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(id=merchant.id)

This serialized balance checks safely.

Additional Notes
Background Processing

Implemented with Celery:

process_payout → Simulates settlement
retry_stuck_payouts → Scheduled by Celery Beat every 30s
Retry Strategy

Exponential backoff:

30 * (2 ** attempt_count)
Tests Included
Concurrency test
Idempotency test
What I Focused On

I prioritized:

Correctness over feature quantity
Database integrity over UI polish
Real-world payment system constraints over abstractions
