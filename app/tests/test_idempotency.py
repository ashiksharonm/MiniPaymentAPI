"""Regression tests for idempotency-key scoping, payload fingerprinting and cached money types."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core import redis_client


class FakeRedis:
    """Minimal in-memory stand-in for the Redis calls the service makes."""

    def __init__(self):
        self.store: dict[str, str] = {}

    def get(self, name):
        return self.store.get(name)

    def setex(self, name, time, value):
        self.store[name] = value


@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    fake = FakeRedis()
    monkeypatch.setattr(redis_client, "get_redis_client", lambda: fake)
    return fake


def _make_user(client: TestClient, headers: dict, email: str) -> str:
    resp = client.post(
        "/users", json={"name": "U", "email": email, "country": "US"}, headers=headers
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _txn(user_id: str, key: str, amount: str = "100.00") -> dict:
    return {
        "user_id": user_id,
        "amount": amount,
        "source_currency": "USD",
        "target_currency": "INR",
        "idempotency_key": key,
    }


def test_same_key_different_users_creates_separate_transactions(client, api_headers):
    u1 = _make_user(client, api_headers, "a@example.com")
    u2 = _make_user(client, api_headers, "b@example.com")

    r1 = client.post("/transactions", json=_txn(u1, "shared-key"), headers=api_headers)
    r2 = client.post("/transactions", json=_txn(u2, "shared-key"), headers=api_headers)

    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.json()["id"] != r2.json()["id"]
    assert r2.json()["user_id"] == u2


def test_same_key_same_payload_replays_original(client, api_headers):
    u = _make_user(client, api_headers, "a@example.com")
    first = client.post("/transactions", json=_txn(u, "k1"), headers=api_headers)
    second = client.post("/transactions", json=_txn(u, "k1", amount="100.0"), headers=api_headers)
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_same_key_different_payload_is_conflict(client, api_headers):
    u = _make_user(client, api_headers, "a@example.com")
    first = client.post("/transactions", json=_txn(u, "k1"), headers=api_headers)
    assert first.status_code == 201

    second = client.post("/transactions", json=_txn(u, "k1", amount="999.00"), headers=api_headers)
    assert second.status_code == 409


def test_cache_path_is_scoped_per_user_and_checks_fingerprint(client, api_headers, fake_redis):
    u1 = _make_user(client, api_headers, "a@example.com")
    u2 = _make_user(client, api_headers, "b@example.com")

    r1 = client.post("/transactions", json=_txn(u1, "k"), headers=api_headers)
    assert r1.status_code == 201
    assert f"idempotency:{u1}:k" in fake_redis.store

    # Other user with the same key must not be served user 1's cached transaction
    r2 = client.post("/transactions", json=_txn(u2, "k"), headers=api_headers)
    assert r2.status_code == 201 and r2.json()["id"] != r1.json()["id"]

    # Replay from cache with a different payload -> conflict
    r3 = client.post("/transactions", json=_txn(u1, "k", amount="5.00"), headers=api_headers)
    assert r3.status_code == 409


def test_cached_replay_preserves_decimal_precision(client, api_headers, fake_redis):
    u = _make_user(client, api_headers, "a@example.com")
    amount = "1234567.1234"
    first = client.post("/transactions", json=_txn(u, "k", amount=amount), headers=api_headers)
    replay = client.post("/transactions", json=_txn(u, "k", amount=amount), headers=api_headers)

    assert replay.json() == first.json()
    assert Decimal(replay.json()["amount"]) == Decimal(amount)
    # Cached money values are strings, never floats
    import json
    cached = json.loads(fake_redis.store[f"idempotency:{u}:k"])
    for field in ("amount", "fx_rate", "converted_amount"):
        assert isinstance(cached[field], str)
