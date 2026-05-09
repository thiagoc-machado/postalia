from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.subscriptions.services import seed_default_plans


@pytest.fixture(autouse=True)
def seed_plans(db):
    seed_default_plans()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()
