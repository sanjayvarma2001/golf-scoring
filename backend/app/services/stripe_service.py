"""
Stripe integration for the subscription & payment system (PRD section 4).

Every function here fails loudly and cleanly (HTTP 501, not a raw
exception/500) when STRIPE_SECRET_KEY isn't configured, so the rest of the
app - registration, scores, charities, draws, dashboards - stays fully
demoable without a live Stripe account. Wire real keys into .env when one
is available; nothing else in the codebase needs to change.
"""
from typing import Optional

import stripe
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()

PLAN_AMOUNTS = {
    # Used for the no-Stripe-configured local demo fallback and for reporting;
    # real charges are driven by the Stripe price IDs below, not these values.
    "monthly": 15.00,
    "yearly": 150.00,  # discounted vs. 12 * monthly, per PRD "yearly plan (discounted rate)"
}


def _require_stripe() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Stripe is not configured on this environment (STRIPE_SECRET_KEY missing). "
            "Set it in .env to enable real checkout; subscription status can still be set "
            "manually via the admin panel for local demos.",
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(*, plan: str, user_email: str, user_id: str, success_url: str, cancel_url: str) -> str:
    _require_stripe()
    price_id = settings.STRIPE_PRICE_ID_MONTHLY if plan == "monthly" else settings.STRIPE_PRICE_ID_YEARLY
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"No Stripe price configured for the '{plan}' plan.",
        )
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user_email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=user_id,
        metadata={"user_id": user_id, "plan": plan},
    )
    return session.url


def construct_webhook_event(payload: bytes, sig_header: Optional[str]):
    _require_stripe()
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="STRIPE_WEBHOOK_SECRET is not configured")
    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid Stripe webhook: {exc}") from exc


def cancel_subscription(stripe_subscription_id: str) -> None:
    _require_stripe()
    stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)
