DEPLOYMENT READINESS REPORT
Date: 2026-06-24

Overall Go/No-Go: NO-GO for production (see critical blockers)
Estimated production stability score: 58/100

Summary checks
--------------
1) Can the backend run from scratch using only `.env.example`?
- No. The `.env.example` contains placeholders (notably `JWT_SECRET=change_this_secret`) and must be copied to a real `.env` with real secrets and credentials. Also the database schema (models) changed but no migrations are present, so the database will not match models out-of-the-box.

2) Are all required environment variables documented?
- Largely yes. `backend/.env.example` documents:
  - `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `BACKEND_URL`.
- Missing/unclear items to add to docs:
  - Recommended `SENTRY_DSN` / logging/monitoring config (not required by code but recommended).
  - Production-ready `CORS_ALLOWED_ORIGINS` override instead of wildcard `*` (the code currently uses `allow_origins=['*']`).
  - Any DB connection-pool or SQLALCHEMY-specific options (timeouts, pool_size) for production tuning.

3) Can Stripe flow work in test mode end-to-end?
- Yes, in principle:
  - `create_checkout_session` uses `STRIPE_SECRET_KEY` and sets customer metadata. It runs in a threadpool to avoid blocking.
  - `/pay` persists `stripe_customer_id` on the user record.
  - `/webhook` verifies signatures using `STRIPE_WEBHOOK_SECRET` and updates subscription state.
- Requirements to make it actually work end-to-end in test/dev:
  - The backend webhook endpoint must be reachable by Stripe (use `stripe listen` or ngrok in dev).
  - Use Stripe test keys and the corresponding webhook signing secret from the `stripe listen` or dashboard.
  - Ensure database schema includes new subscription fields and `stripe_events` table (migrations pending).

4) Are database migrations required and documented clearly?
- Yes. Required: add new fields to `users` table and add `stripe_events` table. No Alembic configuration or migration files are present in the repo. This is a critical blocker — deploy will fail or raise runtime errors until schema matches models.

5) Any blocking runtime errors risk?
- Potential blocking/failure issues to resolve before production:
  - Shutdown code calls `await engine.dispose()` in `backend/app/main.py`. Depending on SQLAlchemy version, `AsyncEngine.dispose()` may be synchronous; awaiting a non-coroutine will raise an exception on shutdown. Verify correct dispose call (`engine.dispose()` or `await engine.dispose()` depending on SQLAlchemy version) or call `engine.sync_engine.dispose()`.
  - Placeholder secret values in `.env.example` (not a runtime crash but security risk).
  - `CORS` currently allows all origins (`allow_origins=['*']`) — security risk for production.
  - Webhook processing currently swallows processing exceptions and returns 200. This prevents retries for transient server-side failures (may hide delivery problems). Depending on desired retry semantics, you may want to return non-2xx for transient failures.

6) Are async operations safe under load?
- Good aspects:
  - Stripe SDK calls (synchronous) are executed inside `run_in_threadpool`, reducing risk of blocking the event loop for those calls.
  - Redis client uses `redis.asyncio.Redis` (async) and DB uses SQLAlchemy async engine.
- Performance concerns:
  - Heavy webhook volumes or many concurrent Stripe calls may overload the threadpool; consider moving billing operations to a worker queue (Celery, RQ) for heavy loads.
  - No explicit connection pool tuning or timeouts for DB/Redis; defaults may be insufficient under production load and need tuning.

7) Is webhook idempotency truly safe?
- The implementation uses a `stripe_events` table with a unique constraint on `stripe_event_id`. `mark_stripe_event_processed` attempts to insert then catches `IntegrityError` and treats duplicates as already processed.
- This is generally safe for idempotency across concurrent workers, provided the DB enforces the unique constraint transactionally. It is acceptable, but recommendations:
  - Use an atomic DB insert with `ON CONFLICT DO NOTHING` and check affected rows (or equivalent SQLAlchemy pattern) for more explicit atomic behavior.
  - Ensure the `stripe_events` table is created in the DB schema before enabling webhooks.

8) Missing production configurations
- CORS restricted origins (currently '*') — set `CORS_ALLOWED_ORIGINS` and apply.
- Logging & monitoring (Sentry/Prometheus) not configured — add structured logging and error reporting.
- TLS/HTTPS termination not documented — ensure deployment sits behind TLS.
- Rate limiting and webhook verification hardening (ensure webhook route is not abused).
- Resource limits, healthchecks, readiness/liveness probes in Docker compose or K8s manifests absent.

Go / No-Go for production
-------------------------
- Recommendation: NO-GO until critical blockers are resolved.

Critical blockers (must fix before production)
- Database migrations: create and apply Alembic migrations to add new `users` fields (`stripe_customer_id`, `stripe_subscription_id`, `subscription_status`, `plan`, `current_period_end`, `has_active_subscription`) and create `stripe_events` table. (High)
- Secrets: replace placeholder `JWT_SECRET` and other placeholder keys in environment with secure, properly stored secrets. (High)
- Shutdown code: verify and fix `engine.dispose()` usage to avoid exceptions at shutdown. (High)
- CORS: remove wildcard `*` in production; configure allowed origins. (High)

Required fixes before launch
- Add Alembic and migration file(s) to reflect model changes (see above).
- Secure environment: set secure `JWT_SECRET` (>=32 chars) and store secrets in a vault or environment management system.
- Fix shutdown sequence for SQLAlchemy engine disposal. Verify Redis client close calls as appropriate.
- Harden webhook error handling policy (decide whether to return non-2xx on transient processing failure to allow Stripe retries).
- Add production logging, monitoring, and SLO/alerting for billing/webhook failures.
- Add connection pool and timeout tuning for database and Redis.
- Add healthchecks and container probes for Docker/Kubernetes deployment.

Estimated production stability score: 58/100
- Rationale: Core functionality implemented and Stripe flows present with idempotency, but missing migrations, insecure defaults, and production-hardening items reduce readiness significantly.

Deliverables created
- backend/DEPLOYMENT_READINESS_REPORT.md (this file)

Stopping — no code changes were made.
