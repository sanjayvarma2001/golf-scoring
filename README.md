# Digital Heroes — Golf Scoring, Draws & Charity Platform

Implementation of the Digital Heroes Level 1 PRD: a subscription-driven platform combining
Stableford score tracking, a monthly number-match prize draw, and a charity contribution system.

For a stage-by-stage walkthrough of how this was built and why, see
[docs/IMPLEMENTATION_PIPELINE.md](docs/IMPLEMENTATION_PIPELINE.md).

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + Alembic. Runs against SQLite with zero setup
  locally, and against PostgreSQL (Supabase) in production via the same code, by swapping
  `DATABASE_URL`.
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS 4.
- **Auth**: JWT bearer tokens (role + user id embedded in the token), bcrypt password hashing.
- **Payments**: Stripe Checkout, with a documented no-Stripe-configured fallback so the whole
  app is demoable without a live Stripe account (see "Ambiguities" below).

## Project layout

```
backend/    FastAPI app, SQLAlchemy models, Alembic migrations, seed script
frontend/   Next.js app (App Router)
```

## Running locally

### Backend

```
cd backend
venv/Scripts/pip install -r requirements.txt   # if not already installed
cp .env.example .env                           # then set JWT_SECRET_KEY and ADMIN_PASSWORD - required, no default
venv/Scripts/python -m alembic upgrade head
venv/Scripts/python seed.py                     # creates sample charities + an admin account
venv/Scripts/python -m uvicorn app.main:app --reload --port 8010
```

API docs: `http://127.0.0.1:8010/docs`. Log in with the `ADMIN_USERNAME` / `ADMIN_PASSWORD` you
set in `.env`.

### Frontend

```
cd frontend
npm install
cp .env.example .env.local     # points at the local backend by default
npm run dev
```

Then open `http://localhost:3000`.

## What's implemented

Every domain in the PRD has working models, API routes, and a UI screen, not just the base
auth/schema layer:

- **Auth**: register/login, bcrypt hashing, JWT with expiry, role-based route guards.
- **Scores**: 1-45 Stableford range and one-entry-per-date enforced at the database level
  (`CheckConstraint` / `UniqueConstraint`), not just in request validation. Only the latest 5
  scores are retained; a new entry evicts the oldest.
- **Charities**: public directory with search/filter, profile pages with images and events,
  homepage spotlight, full admin CRUD.
- **Subscriptions**: monthly/yearly plans, Stripe Checkout integration with webhook handling,
  lifecycle states (inactive/active/cancelled/lapsed).
- **Draws**: admin-configurable random or algorithmic draw logic, simulate-before-publish,
  automatic prize-pool calculation (40/35/25% split), equal split among same-tier winners,
  5-match jackpot rollover across months.
- **Winners**: proof-of-score upload, admin approve/reject, pending → paid payout tracking.
- **Donations**: independent one-off donations, separate from the gameplay charity split.
- **Dashboards**: full subscriber dashboard (subscription, scores, charity, participation,
  winnings) and full admin dashboard (users, draws, charities, winners, reports & analytics).

## Ambiguities the PRD left open, and how they were resolved

The PRD explicitly says "ambiguity is part of the test." Two decisions were made deliberately
rather than left to guesswork, and are documented in code comments at their source:

1. **Database engine**: the deliverables table calls Supabase an example, but the deployment
   constraints state it flatly ("use a new Supabase project"). Built on PostgreSQL/SQLAlchemy
   accordingly (see `backend/app/database/db.py`), rather than the MongoDB the project
   initially started with.
2. **Draw mechanism**: the PRD names match tiers (3/4/5-number) and pool shares but never
   specifies how a subscriber gets numbers or how a draw actually resolves. Implemented as: every
   active subscriber is auto-issued a 5-number ticket (1-49) each draw; "random" mode draws
   winning numbers uniformly; "algorithmic" mode weights the draw toward numbers held by
   higher-average-scoring subscribers. Full reasoning is in
   `backend/app/services/draw_engine.py`.

Stripe is real (Checkout Session creation + webhook signature verification), but every
Stripe-dependent endpoint returns a clean `501` with an explanation when no Stripe keys are
configured, and subscriptions activate directly instead for local demos - so the rest of the
platform (scores, draws, charity math, dashboards) is fully testable without a Stripe account.
Wire real keys into `backend/.env` and nothing else needs to change.

## Deployment

- **Frontend** → Vercel, as the PRD specifies. Set `NEXT_PUBLIC_API_URL` to the deployed
  backend's `/api/v1` URL.
- **Backend** → a Python-capable host (Render, Railway, Fly.io). Vercel's Python runtime isn't
  a good fit for a persistent async FastAPI app with database connection pooling; pairing a
  Next.js-on-Vercel frontend with a separately hosted API is the standard shape for this stack.
- **Database** → a new Supabase project. Use the **pooled** connection string (port 6543) as
  `DATABASE_URL` on a serverless/autoscaling host, run `alembic upgrade head` once against it,
  then `python seed.py` to create the initial charities and admin account.

## Known simplifications, given the timeline

- UI is clean and fully functional but doesn't yet have the extensive micro-interaction/motion
  polish the PRD's UI/UX section asks for - functionality was prioritized over animation given
  the time already spent on the original MongoDB-based scaffold.
- Draw ticket numbers are re-generated per draw rather than persisting across months.
- No automated test suite yet; correctness was verified with a full manual smoke test of every
  endpoint (auth, scores, charities, subscriptions, the full draw lifecycle including jackpot
  rollover, winner verification/payout, donations, and admin reports) against a live server -
  see the conversation history for the exact requests run. Adding `pytest` coverage for
  `app/services/draw_engine.py` (pure functions, no DB needed) would be the highest-value next
  step.
