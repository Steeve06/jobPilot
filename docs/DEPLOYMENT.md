# JobPilot — Deployment Guide

## Current Status: Local Docker Only

Everything in this project has been built and tested for local use via
`docker compose up`. It has **not** been deployed to a real server. This
guide covers what changes when you're ready to do that.

## Prerequisites for a Real Deployment

1. A small VM or PaaS (a $5-10/month VPS is genuinely enough at this scale — DigitalOcean, Hetzner, Railway, Render, Fly.io are all reasonable).
2. A domain name (even a cheap one) — needed for real HTTPS.
3. Real Redis — **do not use Memurai Developer Edition in production** (its license explicitly forbids this, see Sprint 14/19 notes). Use genuine open-source Redis on a Linux host, or a managed Redis service.

## Steps

### 1. Flip production security settings
In `backend/.env` (the deployed server's copy, not your local one):
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
ALLOWED_HOSTS=yourdomain.com
```

### 2. Update CORS/CSRF trusted origins
`backend/config/settings.py`'s `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS` currently only list `localhost` variants — add your real domain.

### 3. Update Google OAuth redirect URIs
Add your real domain's callback URL in Google Cloud Console, alongside (or instead of) the `localhost` ones — same exact pattern as the Sprint 16 debugging, just with your real domain.

### 4. Deploy via Docker Compose
The existing `docker-compose.yml` is deployment-ready as-is — point your VM at the repo, set the real `.env` files, run:

docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser


### 5. Put a reverse proxy in front (for real HTTPS)
Nginx or Caddy in front of the `frontend`/`backend` containers, with Let's Encrypt for a free TLS certificate. Caddy is the simpler option (automatic HTTPS with minimal config) if you've never set this up before.

### 6. Point Celery Beat's schedule at the real timezone if needed
`CELERY_TIMEZONE` currently inherits Django's `TIME_ZONE` — confirm it's what you want for a server that might not be in your local timezone.

## What NOT to change
The Dockerfiles, `docker-compose.yml` structure, and the app code itself need no changes for deployment — this was deliberately built so "works locally in Docker" and "works on a real server" are the same artifact, per the original NFR Portability goal from Sprint 0.