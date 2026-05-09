# Postalia

Postalia is a dockerized SaaS MVP for generating Instagram content with AI.

## Features

- JWT authentication with Google OAuth and optional local email/password auth
- Google-only mode controlled by `GOOGLE_ONLY`
- Brand/company profiles and reusable brand templates
- Instagram post generation: captions, hashtags, carousel outlines, image prompts and full post packages
- Optional image generation with output format selection
- Plan limits and points wallet with audit trail
- Page ad slots for free users and optional rewarded ads
- Referral rewards with anti-abuse checks
- Creem billing integration with webhook-driven subscription updates
- Staff-only internal endpoints instead of Django Admin
- Swagger/OpenAPI at `/api/schema/` and `/api/docs/`
- Multilingual frontend: English, Spanish, Portuguese

## Tech Stack

- Backend: Django 6, Django REST Framework, SimpleJWT, PostgreSQL, Celery, Redis, drf-spectacular
- Frontend: Vue 3, TypeScript, Vite, Vuetify, Pinia, Vue Router, vue-i18n
- Infra: Docker Compose, MinIO-compatible storage, local demo AI service

## Architecture Overview

- `backend/`: Django project and domain apps
- `frontend/`: Vue SPA
- `tools/demo-ai/`: local fake AI container for deterministic text and image placeholders
- `docker-compose.yml`: PostgreSQL, Redis, backend, frontend, Celery worker, MinIO, demo AI service

## Folder Structure

- `backend/apps/accounts`: custom user, JWT auth, Google login, auth config
- `backend/apps/brands`: brands and templates
- `backend/apps/subscriptions`: plans and subscriptions
- `backend/apps/credits`: wallet, transactions and rewards
- `backend/apps/generations`: generation requests and preview/export flows
- `backend/apps/ai_providers`: fake and real AI provider abstraction
- `backend/apps/referrals`: referral rewards
- `backend/apps/ads`: rewarded ad events
- `backend/apps/risk`: device sessions and risk events
- `backend/apps/exports`: post exports
- `backend/apps/staff`: staff-only management endpoints

## Environment Variables

Copy `.env.example` to `.env` and adjust the values.

### Backend

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `INITIAL_STAFF_EMAIL`
- `INITIAL_STAFF_PASSWORD`
- `INITIAL_STAFF_NAME`
- `GOOGLE_ONLY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `AI_PROVIDER_MODE` (`fake` or `real`)
- `ENABLE_FAKE_AI_IN_PRODUCTION`
- `AI_TEXT_PROVIDER`
- `AI_TEXT_API_KEY`
- `AI_TEXT_MODEL`
- `AI_IMAGE_PROVIDER`
- `AI_IMAGE_API_KEY`
- `AI_IMAGE_MODEL`
- `DEMO_AI_BASE_URL`
- `ENABLE_PAGE_ADS`
- `ENABLE_REWARDED_ADS`
- `ADS_PROVIDER`
- `GOOGLE_ADSENSE_CLIENT_ID`
- `GOOGLE_ADSENSE_SLOT_HEADER`
- `GOOGLE_ADSENSE_SLOT_SIDEBAR`
- `GOOGLE_ADSENSE_SLOT_DASHBOARD`
- `GOOGLE_ADSENSE_SLOT_FOOTER`
- `REWARDED_AD_PROVIDER`
- `REWARDED_AD_POINTS`
- `REWARDED_AD_DAILY_LIMIT`
- `CREEM_ENABLED`
- `CREEM_ENVIRONMENT`
- `CREEM_API_KEY`
- `CREEM_WEBHOOK_SECRET`
- `CREEM_API_BASE_URL_TEST`
- `CREEM_API_BASE_URL_PRODUCTION`
- `CREEM_SUCCESS_URL`
- `CREEM_CANCEL_URL`
- `CREEM_PORTAL_RETURN_URL`
- `CREEM_STARTER_PRODUCT_ID`
- `CREEM_PRO_PRODUCT_ID`
- `CREEM_AGENCY_PRODUCT_ID`
- `PAYMENT_WEBHOOK_ALLOWED_SKEW_SECONDS`
- `USE_S3_STORAGE`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_ENDPOINT_URL`
- `AWS_S3_CUSTOM_DOMAIN`
- `AWS_S3_ACCESS_KEY_ID`
- `AWS_S3_SECRET_ACCESS_KEY`
- `APP_BASE_URL`
- `FRONTEND_BASE_URL`
- `DEFAULT_LANGUAGE`
- `ENABLE_DEV_FAKE_AD_REWARDS`

### Frontend

- `VITE_API_BASE_URL`
- `VITE_APP_NAME`
- `VITE_DEFAULT_LANGUAGE`
- `VITE_GOOGLE_CLIENT_ID`
- `VITE_ENABLE_PAGE_ADS`
- `VITE_ENABLE_REWARDED_ADS`
- `VITE_ADS_PROVIDER`
- `VITE_GOOGLE_ADSENSE_CLIENT_ID`
- `VITE_GOOGLE_ADSENSE_SLOT_HEADER`
- `VITE_GOOGLE_ADSENSE_SLOT_SIDEBAR`
- `VITE_GOOGLE_ADSENSE_SLOT_DASHBOARD`
- `VITE_GOOGLE_ADSENSE_SLOT_FOOTER`
- `VITE_CREEM_ENABLED`
- `VITE_REWARDED_AD_PROVIDER`
- `VITE_REWARDED_AD_POINTS`
- `VITE_REWARDED_AD_DAILY_LIMIT`

## How to Run Locally

For a development workflow with hot reload:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Use the default compose file alone when you want the production-like container set:

```bash
docker compose up --build
```

## Makefile Shortcuts

```bash
make up-dev
make up-prod
make down
make reload
make test-back
make test-front
make tests
make migrate
make logs
```

- `make up-dev` starts the development stack with hot reload.
- `make up-prod` starts the production-like stack from the base compose file.
- `make reload` restarts the application services without tearing down the stack.
- `make test-back` runs the backend test suite in the container.
- `make test-front` runs the frontend test suite in the container.
- `make tests` runs both test suites sequentially.

Services:

- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/api/docs/`
- Frontend: `http://localhost:5173`
- MinIO console: `http://localhost:9001`
- Demo AI service: `http://localhost:8001`

## First Staff User

The backend creates the initial staff user on startup using:

- `INITIAL_STAFF_EMAIL`
- `INITIAL_STAFF_PASSWORD`
- `INITIAL_STAFF_NAME`

The bootstrap command also seeds the default plans.

## Migrations

```bash
docker compose exec backend python manage.py migrate --run-syncdb
```

The container entrypoint already runs migrations automatically.
If the database was partially initialized before a crash or interrupted deploy, use the recovery command once:

```bash
docker compose exec backend python manage.py fake_initial_migrate
```

Use that recovery command only when tables already exist but the migration history is missing entries.

## Tests

```bash
docker compose exec backend python -m pytest
docker compose exec frontend npm run test:run
```

## Swagger

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Plans and Points

- Plans: `free`, `starter`, `pro`, `agency`
- Every points mutation creates a `CreditTransaction`
- Wallet balance is never updated directly
- Spending is done in a database transaction
- Free plan limits:
  - 3 free text generations per month
  - text generation costs 5 points after the free quota
  - image generation costs 30 points
  - maximum 1 image generation per day
  - rewarded ad completion gives 5 points
  - maximum 2 rewarded ads per day

## AI Provider Abstraction

- `AI_PROVIDER_MODE=fake`: deterministic local outputs, no external API calls
- `AI_PROVIDER_MODE=real`: provider-specific keys are required and validated at startup
- Real text providers can be configured through `AI_TEXT_PROVIDER`
- Real image providers are prepared but optional

## Fake AI in Development

- The fake mode uses the local `demo-ai` container when available
- If the container is unavailable, the backend falls back to deterministic in-process output
- The fake image flow returns a local placeholder image URL

## Rewarded Ads Simulation

- Enable with `ENABLE_REWARDED_ADS=true`
- Local/dev simulation endpoint: `POST /api/rewards/ads/complete/`
- Status endpoint: `GET /api/rewards/ads/status/`
- Mock completion is only available when `ENABLE_DEV_FAKE_AD_REWARDS=true`
- Production must keep `ENABLE_DEV_FAKE_AD_REWARDS=false`
- Duplicate events are blocked through `external_event_id`
- Daily limits are enforced on the backend before points are awarded

## Page Ads

- Enable page ad slots with `ENABLE_PAGE_ADS=true`
- Use `ADS_PROVIDER=mock` for local development
- Use `ADS_PROVIDER=google_adsense` with the AdSense client and slot IDs in production
- Ad slots appear on the landing page, pricing page, wallet, dashboard for free users and history for free users
- Paid users do not see page ads by default

## Creem Billing

- Set `CREEM_ENABLED=true` to enable paid subscriptions
- Use `CREEM_ENVIRONMENT=test` for the sandbox API and `production` for live billing
- Configure `CREEM_API_KEY`, `CREEM_WEBHOOK_SECRET` and the paid plan product IDs
- Checkout starts with `POST /api/billing/checkout/`
- Current billing snapshot is returned by `GET /api/billing/subscription/`
- Billing portal is returned by `POST /api/billing/portal/`
- Webhooks are handled at `POST /api/webhooks/creem/`
- Webhooks are the source of truth for plan activation, cancellation and expiry
- The frontend success page is only a UX confirmation state

## Security Notes

- No secrets are hardcoded
- JWT refresh is stored in an `HttpOnly` cookie
- Every API checks user ownership and permissions
- Google-only mode disables local login/register in the backend and hides those fields in the frontend
- Rate limiting is enabled on auth, generation, referrals and ads
- Suspicious prompts are blocked by a basic moderation layer
- Rewarded ads and referrals have anti-abuse checks

## Deployment Notes

- Use `DJANGO_DEBUG=false`
- Set a strong `DJANGO_SECRET_KEY`
- Configure `DJANGO_ALLOWED_HOSTS`
- Configure `DJANGO_CORS_ALLOWED_ORIGINS`
- Use HTTPS and secure cookies
- Configure real AI providers
- Configure a real ad provider callback flow
- Configure real email delivery
- Configure backups and monitoring
- Add a real payment provider later

## Production Checklist

- [ ] `DJANGO_DEBUG=false`
- [ ] Strong `DJANGO_SECRET_KEY`
- [ ] `DJANGO_ALLOWED_HOSTS`
- [ ] `DJANGO_CORS_ALLOWED_ORIGINS`
- [ ] HTTPS enabled
- [ ] Secure cookies enabled
- [ ] Real AI providers configured
- [ ] `AI_PROVIDER_MODE=real` or explicit fake override with `ENABLE_FAKE_AI_IN_PRODUCTION=true`
- [ ] `CREEM_ENABLED=true`
- [ ] `CREEM_ENVIRONMENT=production`
- [ ] Real `CREEM_API_KEY`
- [ ] Real `CREEM_WEBHOOK_SECRET`
- [ ] Real Creem product IDs configured
- [ ] Fake ad reward endpoint disabled
- [ ] `ENABLE_DEV_FAKE_AD_REWARDS=false`
- [ ] Real ad provider callbacks configured
- [ ] Real AdSense slots configured if page ads are enabled
- [ ] Email provider configured
- [ ] Monitoring/logging configured
- [ ] Backups configured
- [ ] Rate limits reviewed
- [ ] GDPR/privacy reviewed
- [ ] Real payment provider integrated

## Future Roadmap

- Stripe/Paddle/Cream payment integration
- Batch generation and editorial calendar automation
- Real image provider integration
- Email verification and recovery flows
- Export formats beyond PNG
- Better risk scoring and abuse review workflows
- Data export/delete workflows for GDPR
