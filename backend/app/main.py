"""Self-Service Kafka Ingestion Portal - API gateway."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import User
from .routers import auth_router, health, topics

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)

DEMO_USERS = [
    ("admin", "admin123", "admin"),
    ("producer", "producer123", "producer"),
    ("viewer", "viewer123", "viewer"),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).count():
            for username, password, role in DEMO_USERS:
                db.add(User(username=username,
                            password_hash=hash_password(password), role=role))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="Kafka Ingestion Portal", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(auth_router.router)
app.include_router(topics.router)
