"""Integration tests: Snowflake landing preview through the API."""


def test_preview_maps_types_and_flags_contract_drift(client, producer_headers, orders_topic):
    resp = client.post("/api/topics/orders.v1/preview", headers=producer_headers, json={
        "sample_payloads": [
            {"order_id": "A-100", "amount": 12.5,
             "created_at": "2026-07-01T10:00:00Z"},
            {"order_id": "A-101", "amount": "not-a-number",
             "metadata": {"channel": "web"}},
        ]
    })
    assert resp.status_code == 200
    body = resp.json()

    cols = {c["name"]: c["snowflake_type"] for c in body["columns"]}
    assert cols["ORDER_ID"] == "VARCHAR"
    assert cols["AMOUNT"] == "FLOAT"
    assert cols["CREATED_AT"] == "TIMESTAMP_NTZ"
    assert cols["METADATA"] == "VARIANT"          # nested object -> VARIANT

    # bad float coerced to NULL with a warning; extra field flagged
    assert body["rows"][1]["AMOUNT"] == "NULL"
    assert any("not in the registered schema" in w for w in body["warnings"])
    assert any("could not coerce" in w for w in body["warnings"])

    assert "CREATE TABLE IF NOT EXISTS RAW.ORDERS_V1" in body["create_table_ddl"]
    assert "COPY INTO RAW.ORDERS_V1" in body["copy_into_sql"]
    assert "@KAFKA_STAGE/orders.v1/" in body["copy_into_sql"]


def test_preview_timestamp_lands_ntz(client, producer_headers, orders_topic):
    resp = client.post("/api/topics/orders.v1/preview", headers=producer_headers, json={
        "sample_payloads": [{"order_id": "A-1", "amount": 1.0,
                             "created_at": "2026-07-01T10:00:00Z"}]
    })
    assert resp.json()["rows"][0]["CREATED_AT"] == "2026-07-01 10:00:00"
