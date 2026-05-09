from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class CreemCheckoutResult:
    checkout_url: str
    raw_response: dict[str, Any]


@dataclass(frozen=True)
class CreemPortalResult:
    customer_portal_link: str
    raw_response: dict[str, Any]


class CreemProvider:
    def __init__(self, api_key: str, base_url: str, webhook_secret: str, timeout: int = 15):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.webhook_secret = webhook_secret
        self.timeout = timeout

    def create_checkout_session(
        self,
        *,
        product_id: str,
        success_url: str,
        cancel_url: str,
        customer_email: str,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> CreemCheckoutResult:
        payload: dict[str, Any] = {
            "product_id": product_id,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "customer": {"email": customer_email},
        }
        if metadata:
            payload["metadata"] = metadata
        if request_id:
            payload["request_id"] = request_id
        response = requests.post(
            f"{self.base_url}/checkouts",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        checkout_url = data.get("checkout_url")
        if not checkout_url:
            raise RuntimeError("Creem checkout response missing checkout_url.")
        return CreemCheckoutResult(checkout_url=checkout_url, raw_response=data)

    def create_customer_portal(self, customer_id: str, return_url: str | None = None) -> CreemPortalResult:
        payload: dict[str, Any] = {"customer_id": customer_id}
        if return_url:
            payload["return_url"] = return_url
        response = requests.post(
            f"{self.base_url}/customers/billing",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        portal_link = data.get("customer_portal_link")
        if not portal_link:
            raise RuntimeError("Creem portal response missing customer_portal_link.")
        return CreemPortalResult(customer_portal_link=portal_link, raw_response=data)

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str | None, timestamp_header: str | None = None, allowed_skew_seconds: int | None = None) -> bool:
        if not signature_header:
            return False

        expected = hmac.new(self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        provided = signature_header.strip()

        if "," in provided or "=" in provided:
            parts = {}
            for chunk in provided.split(","):
                if "=" not in chunk:
                    continue
                key, value = chunk.split("=", 1)
                parts[key.strip()] = value.strip()
            provided = parts.get("v1") or parts.get("signature") or parts.get("hash") or provided
            timestamp_header = timestamp_header or parts.get("t") or parts.get("timestamp")

        if timestamp_header and allowed_skew_seconds is not None:
            try:
                timestamp = int(timestamp_header)
            except ValueError:
                return False
            import time

            if abs(int(time.time()) - timestamp) > allowed_skew_seconds:
                return False

        return hmac.compare_digest(expected, provided)

    @staticmethod
    def parse_json(raw_body: bytes) -> dict[str, Any]:
        return json.loads(raw_body.decode("utf-8"))

    def _headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }
