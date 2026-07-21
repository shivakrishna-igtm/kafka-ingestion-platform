"""Integration tests: full API flows through auth, registration, evolution."""
from tests.conftest import ORDERS_SCHEMA


def test_login_bad_password_rejected(client):
    resp = client.post("/api/auth/login",
                       json={"username": "producer", "password": "wrong"})
    assert resp.status_code == 401


def test_topics_require_auth(client):
    assert client.get("/api/topics").status_code == 401


def test_viewer_cannot_register_topic(client, viewer_headers):
    resp = client.post("/api/topics", headers=viewer_headers, json={
        "name": "sneaky.topic", "schema_definition": ORDERS_SCHEMA,
    })
    assert resp.status_code == 403


def test_register_and_fetch_topic(client, producer_headers, orders_topic):
    assert orders_topic["latest_version"] == 1
    resp = client.get("/api/topics/orders.v1", headers=producer_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "orders.v1"
    assert len(body["schemas"]) == 1


def test_duplicate_topic_rejected(client, producer_headers, orders_topic):
    resp = client.post("/api/topics", headers=producer_headers, json={
        "name": "orders.v1", "schema_definition": ORDERS_SCHEMA,
    })
    assert resp.status_code == 409


def test_invalid_topic_name_rejected(client, producer_headers):
    resp = client.post("/api/topics", headers=producer_headers, json={
        "name": "Bad Name!", "schema_definition": ORDERS_SCHEMA,
    })
    assert resp.status_code == 422


def test_compatible_evolution_bumps_version(client, producer_headers, orders_topic):
    new_schema = {"fields": [*ORDERS_SCHEMA["fields"],
                             {"name": "coupon", "type": "string", "required": False}]}
    check = client.post("/api/topics/orders.v1/schema/check",
                        headers=producer_headers,
                        json={"schema_definition": new_schema})
    assert check.json()["compatible"] is True

    resp = client.post("/api/topics/orders.v1/schema",
                       headers=producer_headers,
                       json={"schema_definition": new_schema})
    assert resp.status_code == 200
    assert resp.json()["latest_version"] == 2


def test_breaking_evolution_rejected(client, producer_headers, orders_topic):
    broken = {"fields": [{"name": "order_id", "type": "int", "required": True}]}
    resp = client.post("/api/topics/orders.v1/schema",
                       headers=producer_headers,
                       json={"schema_definition": broken})
    assert resp.status_code == 422
    assert "breaking_changes" in resp.json()["detail"]


def test_health_endpoints(client):
    assert client.get("/healthz").json()["status"] == "alive"
    ready = client.get("/readyz").json()
    assert ready["checks"]["database"] == "ok"
