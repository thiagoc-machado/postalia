from __future__ import annotations

from django.utils import timezone

from .models import DeviceSession, RiskEvent


def upsert_device_session(user, ip_address: str | None, user_agent: str | None, device_id: str | None = "") -> DeviceSession:
    session, _ = DeviceSession.objects.get_or_create(
        user=user,
        device_id=device_id or "",
        defaults={
            "ip_address": ip_address,
            "user_agent": user_agent or "",
            "last_seen_at": timezone.now(),
        },
    )
    session.ip_address = ip_address
    session.user_agent = user_agent or ""
    session.last_seen_at = timezone.now()
    session.save(update_fields=["ip_address", "user_agent", "last_seen_at"])
    return session


def log_risk_event(user=None, ip_address: str | None = None, device_id: str | None = "", event_type: str = "", severity: str = "low", metadata: dict | None = None) -> RiskEvent:
    return RiskEvent.objects.create(
        user=user,
        ip_address=ip_address,
        device_id=device_id or "",
        event_type=event_type,
        severity=severity,
        metadata=metadata or {},
    )
