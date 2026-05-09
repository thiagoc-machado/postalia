from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False),
    GOOGLE_ONLY=(bool, True),
    ENABLE_FAKE_AI_IN_PRODUCTION=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DJANGO_DEBUG", default=env("DEBUG"))
SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
GOOGLE_ONLY = env("GOOGLE_ONLY", default=True)
ENABLE_FAKE_AI_IN_PRODUCTION = env("ENABLE_FAKE_AI_IN_PRODUCTION", default=False)
ENABLE_DEV_FAKE_AD_REWARDS = env("ENABLE_DEV_FAKE_AD_REWARDS", default=DEBUG)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ALLOWED_ORIGINS", default=[])
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")
APP_BASE_URL = env("APP_BASE_URL", default="http://localhost:8000")
DEFAULT_LANGUAGE = env("DEFAULT_LANGUAGE", default="en")
ENABLE_PAGE_ADS = env("ENABLE_PAGE_ADS", default=False)
ENABLE_REWARDED_ADS = env("ENABLE_REWARDED_ADS", default=False)
ADS_PROVIDER = env("ADS_PROVIDER", default="mock")
GOOGLE_ADSENSE_CLIENT_ID = env("GOOGLE_ADSENSE_CLIENT_ID", default="")
GOOGLE_ADSENSE_SLOT_HEADER = env("GOOGLE_ADSENSE_SLOT_HEADER", default="")
GOOGLE_ADSENSE_SLOT_SIDEBAR = env("GOOGLE_ADSENSE_SLOT_SIDEBAR", default="")
GOOGLE_ADSENSE_SLOT_DASHBOARD = env("GOOGLE_ADSENSE_SLOT_DASHBOARD", default="")
GOOGLE_ADSENSE_SLOT_FOOTER = env("GOOGLE_ADSENSE_SLOT_FOOTER", default="")

REWARDED_AD_PROVIDER = env("REWARDED_AD_PROVIDER", default="mock")
REWARDED_AD_POINTS = env.int("REWARDED_AD_POINTS", default=5)
REWARDED_AD_DAILY_LIMIT = env.int("REWARDED_AD_DAILY_LIMIT", default=2)

CREEM_ENABLED = env("CREEM_ENABLED", default=False)
CREEM_ENVIRONMENT = env("CREEM_ENVIRONMENT", default="test")
CREEM_API_KEY = env("CREEM_API_KEY", default="")
CREEM_WEBHOOK_SECRET = env("CREEM_WEBHOOK_SECRET", default="")
CREEM_API_BASE_URL_TEST = env("CREEM_API_BASE_URL_TEST", default="https://test-api.creem.io/v1")
CREEM_API_BASE_URL_PRODUCTION = env("CREEM_API_BASE_URL_PRODUCTION", default="https://api.creem.io/v1")
CREEM_API_BASE_URL = (
    CREEM_API_BASE_URL_TEST if CREEM_ENVIRONMENT == "test" else CREEM_API_BASE_URL_PRODUCTION if CREEM_ENVIRONMENT == "production" else ""
)
CREEM_SUCCESS_URL = env("CREEM_SUCCESS_URL", default=f"{FRONTEND_BASE_URL}/billing/success")
CREEM_CANCEL_URL = env("CREEM_CANCEL_URL", default=f"{FRONTEND_BASE_URL}/billing/cancel")
CREEM_PORTAL_RETURN_URL = env("CREEM_PORTAL_RETURN_URL", default=f"{FRONTEND_BASE_URL}/subscription")
CREEM_STARTER_PRODUCT_ID = env("CREEM_STARTER_PRODUCT_ID", default="")
CREEM_PRO_PRODUCT_ID = env("CREEM_PRO_PRODUCT_ID", default="")
CREEM_AGENCY_PRODUCT_ID = env("CREEM_AGENCY_PRODUCT_ID", default="")
PAYMENT_WEBHOOK_ALLOWED_SKEW_SECONDS = env.int("PAYMENT_WEBHOOK_ALLOWED_SKEW_SECONDS", default=300)

if not SECRET_KEY:
    SECRET_KEY = "unsafe-development-key" if DEBUG else ""

if not DEBUG and not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured when DEBUG is false.")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "storages",
    "apps.accounts",
    "apps.brands",
    "apps.subscriptions",
    "apps.credits",
    "apps.generations",
    "apps.ai_providers",
    "apps.common",
    "apps.payments",
    "apps.referrals",
    "apps.ads",
    "apps.risk",
    "apps.exports",
    "apps.staff",
]

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "postalia.urls"
WSGI_APPLICATION = "postalia.wsgi.application"
ASGI_APPLICATION = "postalia.asgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"postgres://{env('POSTGRES_USER', default='postalia')}:{env('POSTGRES_PASSWORD', default='postalia')}@{env('POSTGRES_HOST', default='postgres')}:{env('POSTGRES_PORT', default='5432')}/{env('POSTGRES_DB', default='postalia')}",
    )
}

REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = DEFAULT_LANGUAGE
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

if env("USE_S3_STORAGE", default=False):
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="postalia")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
    AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID", default="")
    AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY", default="")
    AWS_S3_ADDRESSING_STYLE = "path"
    AWS_DEFAULT_ACL = None
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", default="60/min"),
        "user": env("THROTTLE_USER", default="600/min"),
        "auth": env("THROTTLE_AUTH", default="10/min"),
        "generation": env("THROTTLE_GENERATION", default="20/min"),
        "referral": env("THROTTLE_REFERRAL", default="10/min"),
        "ads": env("THROTTLE_ADS", default="10/min"),
        "billing": env("THROTTLE_BILLING", default="5/min"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Postalia API",
    "DESCRIPTION": "API do MVP Postalia.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", 30)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
    ("pt", "Português"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")

AI_PROVIDER_MODE = env("AI_PROVIDER_MODE", default="fake")
AI_TEXT_PROVIDER = env("AI_TEXT_PROVIDER", default="")
AI_TEXT_API_KEY = env("AI_TEXT_API_KEY", default="")
AI_TEXT_MODEL = env("AI_TEXT_MODEL", default="")
AI_IMAGE_PROVIDER = env("AI_IMAGE_PROVIDER", default="")
AI_IMAGE_API_KEY = env("AI_IMAGE_API_KEY", default="")
AI_IMAGE_MODEL = env("AI_IMAGE_MODEL", default="")
DEMO_AI_BASE_URL = env("DEMO_AI_BASE_URL", default="http://demo-ai:8001")
DEMO_AI_MODE = env("DEMO_AI_MODE", default="fake")
DEMO_AI_TEXT_MODEL = env("DEMO_AI_TEXT_MODEL", default="")
DEMO_AI_IMAGE_MODEL = env("DEMO_AI_IMAGE_MODEL", default="")
DEMO_AI_DEVICE = env("DEMO_AI_DEVICE", default="cpu")

from apps.ai_providers.services import validate_ai_configuration
from apps.payments.config import validate_payment_configuration

validate_ai_configuration(sys.modules[__name__])
validate_payment_configuration(sys.modules[__name__])

LOCKDOWN_HEADERS = {
    "server": "Postalia",
}

SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

CORS_ALLOW_CREDENTIALS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
