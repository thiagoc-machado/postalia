from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured


def validate_payment_configuration(settings_module) -> None:
    if not getattr(settings_module, "CREEM_ENABLED", False):
        return

    if getattr(settings_module, "CREEM_ENVIRONMENT", "") not in {"test", "production"}:
        raise ImproperlyConfigured("CREEM_ENVIRONMENT must be either 'test' or 'production'.")

    required = [
        "CREEM_API_KEY",
        "CREEM_WEBHOOK_SECRET",
        "CREEM_STARTER_PRODUCT_ID",
        "CREEM_PRO_PRODUCT_ID",
        "CREEM_AGENCY_PRODUCT_ID",
    ]
    missing = [name for name in required if not getattr(settings_module, name, "").strip()]
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ImproperlyConfigured(f"CREEM_ENABLED=true requires these variables: {missing_list}.")


def get_creem_base_url(settings_module) -> str:
    environment = getattr(settings_module, "CREEM_ENVIRONMENT", "test")
    if environment == "test":
        return getattr(settings_module, "CREEM_API_BASE_URL_TEST", "https://test-api.creem.io/v1")
    if environment == "production":
        return getattr(settings_module, "CREEM_API_BASE_URL_PRODUCTION", "https://api.creem.io/v1")
    raise ImproperlyConfigured("CREEM_ENVIRONMENT must be either 'test' or 'production'.")
