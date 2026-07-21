import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_registry.db"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:   # context manager runs startup (seeds demo users)
        yield c


@pytest.fixture()
def producer_headers(client):
    token = client.post("/api/auth/login",
                        json={"username": "producer", "password": "producer123"}
                        ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def viewer_headers(client):
    token = client.post("/api/auth/login",
                        json={"username": "viewer", "password": "viewer123"}
                        ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


ORDERS_SCHEMA = {
    "fields": [
        {"name": "order_id", "type": "string", "required": True},
        {"name": "amount", "type": "float", "required": True},
        {"name": "created_at", "type": "timestamp", "required": False},
    ]
}


@pytest.fixture()
def orders_topic(client, producer_headers):
    resp = client.post("/api/topics", headers=producer_headers, json={
        "name": "orders.v1",
        "description": "order events",
        "owner_team": "commerce",
        "schema_definition": ORDERS_SCHEMA,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()
