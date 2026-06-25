**VEX Backend Deployment Guide**

This guide describes steps to prepare and deploy the VEX backend in production. It assumes you will run the FastAPI app as an ASGI service and serve it behind HTTPS. Two deployment options are covered: Render (PaaS) and a VPS running Ubuntu + Nginx + Gunicorn (systemd).

**Prerequisites**
- A running PostgreSQL instance accessible from the backend.
- A running Redis instance for caching (optional but recommended).
- Stripe account with LIVE API keys and webhook endpoint configured.
- Domain with DNS configured for your backend (e.g., api.yourdomain.com).
- TLS certificate (Let's Encrypt recommended) or Render-managed TLS.
- Copy `backend/.env.production.example` → `backend/.env` and populate values.

**Important notes before deploying**
- Do NOT deploy without running DB migrations: model changes require schema updates (`users` new columns + `stripe_events` table).
- Replace placeholder `JWT_SECRET` with a secure random secret (>=32 characters).
- Configure `CORS_ALLOWED_ORIGINS` without wildcards in production.
- Ensure `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` are the LIVE values when switching to production.

**Common preparation steps**
1. Create `.env` from `backend/.env.production.example` and fill secrets.
2. Provision Postgres and Redis; set `DATABASE_URL` and `REDIS_URL` accordingly.
3. Ensure your DNS points `api.yourdomain.com` to the deployment target.
4. Configure Stripe webhook in the dashboard using your public `BACKEND_URL` (e.g., https://api.yourdomain.com/webhook). Capture the webhook signing secret and put it into `STRIPE_WEBHOOK_SECRET`.
5. Secure secrets in a vault or Render environment settings; never commit `.env` to source control.

**A. Render (Recommended for simplicity)**
1. Create a new Web Service in Render.
2. Connect your Git repository and select the `backend` folder (or root if monorepo support available).
3. Set Build Command: `pip install -r requirements.txt` (auto-detected by Render Python service may suffice).
4. Start Command (Render uses `web` process):

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers
   ```

   (Alternative for production concurrency: use Gunicorn with Uvicorn workers — see VPS section.)

5. Add environment variables via Render dashboard (use `backend/.env.production.example` keys):
   - `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `BACKEND_URL`, `CORS_ALLOWED_ORIGINS`, `LOG_LEVEL`, etc.
6. Enable TLS via Render (automatic).
7. In Stripe dashboard, register the webhook endpoint (https://your-render-hostname/webhook) and copy the signing secret to `STRIPE_WEBHOOK_SECRET` in Render.
8. Run DB migrations: you must run Alembic migrations (see `STEP 4` in earlier plan). Render supports a one-off job to run migration commands.

**B. VPS (Ubuntu + Nginx + Gunicorn / Uvicorn workers)**
This is a sample production deploy flow for an Ubuntu VPS.

1. System preparation (on the VPS):

   ```bash
   sudo apt update
   sudo apt install -y python3.12 python3.12-venv python3.12-dev build-essential libpq-dev nginx
   # Install certbot for TLS
   sudo apt install -y certbot python3-certbot-nginx
   ```

2. Create a service user and directory:

   ```bash
   sudo useradd -m -s /bin/bash vex
   sudo mkdir -p /home/vex/app
   sudo chown vex:vex /home/vex/app
   ```

3. Deploy code and create virtualenv (as user `vex`):

   ```bash
   cd /home/vex/app
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r /path/to/repo/backend/requirements.txt
   # Copy code into /home/vex/app (git clone or rsync)
   ```

4. Configure environment (.env):
   - Place your `backend/.env` in `/home/vex/app` or use systemd environment file. Ensure permissions restrict access.

5. Gunicorn systemd service with Uvicorn workers (create `/etc/systemd/system/vex-backend.service`):

   ```ini
   [Unit]
   Description=VEX Backend
   After=network.target

   [Service]
   User=vex
   Group=vex
   WorkingDirectory=/home/vex/app
   EnvironmentFile=/home/vex/app/.env
   ExecStart=/home/vex/app/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 --bind 127.0.0.1:8000 --log-level info
   Restart=always
   LimitNOFILE=65536

   [Install]
   WantedBy=multi-user.target
   ```

   - Adjust worker count (`-w`) based on CPU cores and expected concurrency.

6. Configure Nginx as reverse proxy (example `/etc/nginx/sites-available/vex`):

   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

   Enable site and reload Nginx:

   ```bash
   sudo ln -s /etc/nginx/sites-available/vex /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

7. Obtain TLS certificate with Certbot:

   ```bash
   sudo certbot --nginx -d api.yourdomain.com
   ```

8. Start and enable service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now vex-backend.service
   sudo journalctl -u vex-backend -f
   ```

9. Run migrations (Important):
   - Install Alembic locally (if not present), generate migration that adds new `users` columns and `stripe_events` table, then run `alembic upgrade head` on the production DB.
   - Example one-off command (after Alembic configured):

   ```bash
   source .venv/bin/activate
   alembic upgrade head
   ```

10. Configure Stripe webhook (live):
    - In Stripe Dashboard → Developers → Webhooks, add endpoint `https://api.yourdomain.com/webhook` and subscribe to events:
      - `checkout.session.completed`
      - `invoice.paid`
      - `invoice.payment_failed`
    - Copy the webhook signing secret and set `STRIPE_WEBHOOK_SECRET` in `/home/vex/app/.env`.

**Production safety checklist**
- [ ] `.env` populated with secure secrets and not committed.
- [ ] Alembic migrations created and applied for model changes.
- [ ] `JWT_SECRET` is strong and rotated per policy.
- [ ] `CORS_ALLOWED_ORIGINS` set to exact origins (no `*`). If your app uses the current hard-coded `*`, modify `backend/app/main.py` to read allowed origins from `CORS_ALLOWED_ORIGINS` environment variable and restart.
- [ ] Logging/monitoring (Sentry) configured.
- [ ] Health checks (readiness/liveness) added to orchestration platform.
- [ ] TLS termination configured.
- [ ] Rate limiting and abuse protection in front of webhook endpoint (optional) — ensure Stripe IPs not blocked.

**Stripe LIVE mode checklist**
- Switch `STRIPE_SECRET_KEY` to the live secret (`sk_live_...`).
- Ensure webhook endpoint is registered in Stripe and `STRIPE_WEBHOOK_SECRET` is set to the live signing secret.
- Test with a canary user or in a staging environment before switching live keys.

**Rollback plan**
- Keep DB backups before running migrations.
- Use a blue/green or rolling deployment strategy; keep previous release available to switch back quickly if issues arise.

**Appendix: Code hints (manual, do not apply automatically)**
- CORS: To use environment-controlled CORS, change `backend/app/main.py` middleware initialization to read `CORS_ALLOWED_ORIGINS` and split by comma into a list. Example snippet (add before `app.add_middleware`):

  ```python
  import os
  origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
  if origins:
      allow_origins = [o.strip() for o in origins.split(',') if o.strip()]
  else:
      allow_origins = []
  ```

  Then use `allow_origins=allow_origins` when adding `CORSMiddleware`.

- Engine disposal: verify SQLAlchemy AsyncEngine disposal matches your SQLAlchemy version. If disposal is synchronous, use `engine.sync_engine.dispose()`.

**End of guide**
