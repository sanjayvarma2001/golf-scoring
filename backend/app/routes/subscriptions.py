from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_current_user, require_admin
from app.database.db import get_db
from app.models.subscription import Payment, Subscription
from app.models.user import User
from app.schemas.subscription import CheckoutRequest, CheckoutResponse, SubscriptionPublic
from app.services.stripe_service import PLAN_AMOUNTS, cancel_subscription, construct_webhook_event, create_checkout_session

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
settings = get_settings()


async def _get_or_create_subscription(db: AsyncSession, user: User) -> Subscription:
    # Queried explicitly rather than via `user.subscription` - lazy-loading a
    # relationship attribute isn't safe in async SQLAlchemy without an
    # explicit await, and would raise MissingGreenlet here.
    result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = result.scalar_one_or_none()
    if sub is None:
        sub = Subscription(user_id=user.id, status="inactive")
        db.add(sub)
        await db.flush()
    return sub


@router.get("/me", response_model=SubscriptionPublic)
async def my_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await _get_or_create_subscription(db, current_user)
    return sub


@router.post("/checkout", response_model=CheckoutResponse)
async def start_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Starts a real Stripe Checkout session when Stripe is configured. When it
    isn't (e.g. a local demo with no Stripe account), activates the
    subscription directly so the rest of the app - draws, dashboards,
    charity math - stays testable end to end without a payment provider.
    """
    if not settings.STRIPE_SECRET_KEY:
        sub = await _get_or_create_subscription(db, current_user)
        sub.plan = payload.plan
        sub.status = "active"
        sub.amount = PLAN_AMOUNTS[payload.plan]
        sub.start_date = date.today()
        sub.renewal_date = date.today() + (timedelta(days=365) if payload.plan == "yearly" else timedelta(days=30))
        db.add(Payment(user_id=current_user.id, kind="subscription", amount=sub.amount, status="succeeded"))
        await db.commit()
        return CheckoutResponse(
            checkout_url=None,
            message="Stripe is not configured in this environment, so the subscription was activated directly for demo purposes.",
        )

    url = create_checkout_session(
        plan=payload.plan,
        user_email=current_user.email,
        user_id=current_user.id,
        success_url=f"{settings.FRONTEND_ORIGIN}/dashboard?checkout=success",
        cancel_url=f"{settings.FRONTEND_ORIGIN}/dashboard?checkout=cancelled",
    )
    return CheckoutResponse(checkout_url=url, message="Redirect the user to checkout_url to complete payment")


@router.post("/cancel", response_model=SubscriptionPublic)
async def cancel_my_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await _get_or_create_subscription(db, current_user)
    if sub.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active subscription to cancel")
    if sub.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
        cancel_subscription(sub.stripe_subscription_id)
    sub.status = "cancelled"
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handles checkout.session.completed / subscription updates from Stripe when it's configured."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event = construct_webhook_event(payload, sig_header)

    data = event["data"]["object"]
    event_type = event["type"]

    if event_type == "checkout.session.completed":
        user_id = data.get("client_reference_id") or data.get("metadata", {}).get("user_id")
        plan = data.get("metadata", {}).get("plan", "monthly")
        if user_id:
            user = await db.get(User, user_id)
            if user:
                sub = await _get_or_create_subscription(db, user)
                sub.plan = plan
                sub.status = "active"
                sub.amount = PLAN_AMOUNTS.get(plan, 0.0)
                sub.start_date = date.today()
                sub.renewal_date = date.today() + (timedelta(days=365) if plan == "yearly" else timedelta(days=30))
                sub.stripe_customer_id = data.get("customer")
                sub.stripe_subscription_id = data.get("subscription")
                db.add(Payment(user_id=user.id, kind="subscription", amount=sub.amount, status="succeeded"))
                await db.commit()
    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated") and data.get("status") in (
        "canceled",
        "unpaid",
    ):
        stripe_sub_id = data.get("id")
        result = await db.execute(select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "lapsed"
            await db.commit()

    return {"received": True}


@router.post("/admin/{user_id}/set-active", response_model=SubscriptionPublic)
async def admin_activate_subscription(
    user_id: str,
    plan: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Manual override so admins can demo/test the platform without a live Stripe account."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    sub = await _get_or_create_subscription(db, user)
    sub.plan = plan
    sub.status = "active"
    sub.amount = PLAN_AMOUNTS.get(plan, 15.0)
    sub.start_date = date.today()
    sub.renewal_date = date.today() + (timedelta(days=365) if plan == "yearly" else timedelta(days=30))
    await db.commit()
    await db.refresh(sub)
    return sub
