
import os

from django.conf import settings
from django.core.checks import Error, register


@register()
def security_settings_check(app_configs, **kwargs):
    # Run these checks only when production is explicitly configured.
    if os.environ.get("DJANGO_ENV", "").lower() != "production":
        return []

    errors = []

    if settings.SECRET_KEY == "dev-only-change-this-key-before-deployment":
        errors.append(
            Error("Set DJANGO_SECRET_KEY in production.", id="vault.E001")
        )

    if settings.AUDIT_HMAC_KEY == settings.SECRET_KEY:
        errors.append(
            Error(
                "Set AUDIT_HMAC_KEY separately from DJANGO_SECRET_KEY in production.",
                id="vault.E002",
            )
        )

    if "*" in settings.ALLOWED_HOSTS:
        errors.append(
            Error("Do not use wildcard ALLOWED_HOSTS in production.", id="vault.E003")
        )

    return errors
