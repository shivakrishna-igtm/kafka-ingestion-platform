# Self-Service Kafka Ingestion Portal

A full-stack internal tool where application teams register Kafka topics, evolve
schemas safely, and preview exactly how their payloads will land in Snowflake —
before anything reaches production. Built to replace the manual, ticket-driven
data onboarding flow with self-service.

**Stack:** React (TypeScript) · Python (FastAPI) · gRPC · Kafka (Redpanda) · Redis · Docker · GitHub Actions

## What it does

- **Topic registration** — producers register a topic with a typed schema
  (v1). With a broker configured, the topic is created on Kafka at registration.
- **Schema evolution with guardrails** — proposing a new schema version runs a
  BACKWARD-compatibility check (can the new schema still read every record
  already on the topic?). Safe changes (adding optional fields, widening
  `int → double`) version up; breaking changes (removing fields, type
  narrowing, optional → required) are rejected with a precise explanation.
- **Snowflake landing preview** — paste sample payloads and see the exact
  table shape they'd produce after a staged `COPY INTO`: column names
  uppercased, JSON types mapped to Snowflake types (nested objects → `VARIANT`,
  ISO timestamps → `TIMESTAMP_NTZ`), values coerced, and every mismatch against
  the registered contract flagged as a warning. Generated `CREATE TABLE` DDL
  and `COPY INTO` statements included.
- **Roles** — `viewer` reads, `producer` registers and evolves, `admin`
  everything. JWT auth; write endpoints enforce role checks.

## Architecture

```
┌──────────────┐   REST    ┌──────────────┐   gRPC    ┌───────────────────┐
│  React (TS)  │ ────────► │   FastAPI    │ ────────► │  Preview service  │
│  nginx :3000 │           │  gateway     │           │  (Snowflake       │
└──────────────┘           │  :8000       │           │   mapper) :50051  │
                           │              │           └───────────────────┘
                           │  JWT · RBAC  │
                           │  registry DB │──► SQLite (SQLAlchemy)
                           │  cache       │──► Redis (in-memory fallback)
                           │  topics      │──► Kafka / Redpanda
                           └──────────────┘
```

Every service degrades gracefully: without Redis the cache falls back to
in-memory, without a broker the registry runs standalone, and without the gRPC
service the preview mapper runs in-process — so `pytest` needs zero
infrastructure and `docker compose up` runs the real thing.

## Run it

**Full stack (Docker):**
```bash
docker compose up --build
# UI:       http://localhost:3000
# API docs: http://localhost:8000/docs
```

**Local dev (no Docker):**
```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload            # :8000

# frontend
cd frontend && npm install && npm run dev  # :5173, proxies /api
```

Demo users: `producer / producer123` · `viewer / viewer123` · `admin / admin123`

## Tests

```bash
cd backend && python -m pytest -v
```

17 tests: unit coverage of the compatibility rules, integration coverage of
auth, RBAC, registration, evolution (compatible and breaking), and the
Snowflake preview path — including type coercion and contract-drift warnings.
CI runs the suite, type-checks and builds the frontend, and builds all Docker
images on every push.

## Observability

- Structured JSON logging on every service
- `/healthz` (liveness) and `/readyz` (readiness with dependency checks)
- Docker `HEALTHCHECK`s on backend and preview service

## Notes on the Snowflake model

The preview service models the staged-loading path (files land in a stage,
`COPY INTO` loads the table) rather than connecting to a live account, so the
portal runs anywhere with zero credentials. The mapper implements the real
rules: unquoted identifiers uppercase, semi-structured data lands as
`VARIANT`, ISO timestamps parse to `TIMESTAMP_NTZ`, and un-coercible values
land `NULL` with a warning — the same failures you'd otherwise discover in a
failed overnight load.
