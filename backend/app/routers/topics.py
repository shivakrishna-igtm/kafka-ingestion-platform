import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import cache, kafka_client
from ..auth import current_user, require_role
from ..compatibility import check_backward
from ..database import get_db
from ..models import SchemaVersion, Topic, User
from ..preview_client import preview
from ..schemas import (CompatibilityResult, PreviewRequest, SchemaDefinition,
                       SchemaProposal, SchemaVersionOut, TopicCreate, TopicOut)

log = logging.getLogger("topics")
router = APIRouter(prefix="/api/topics", tags=["topics"])


def _topic_out(t: Topic, include_schemas: bool = False) -> TopicOut:
    latest = max((s.version for s in t.schemas), default=0)
    return TopicOut(
        id=t.id, name=t.name, description=t.description,
        owner_team=t.owner_team, created_by=t.created_by,
        created_at=t.created_at, latest_version=latest,
        schemas=[
            SchemaVersionOut(
                version=s.version,
                definition=SchemaDefinition(**json.loads(s.definition)),
                created_by=s.created_by, created_at=s.created_at,
            )
            for s in t.schemas
        ] if include_schemas else [],
    )


@router.get("", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db), _: User = Depends(current_user)):
    cached = cache.get_json("topics:all")
    if cached:
        return cached
    topics = [_topic_out(t).model_dump() for t in db.query(Topic).all()]
    cache.set_json("topics:all", topics)
    return topics


@router.get("/{name}", response_model=TopicOut)
def get_topic(name: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    t = db.query(Topic).filter(Topic.name == name).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"topic '{name}' not found")
    return _topic_out(t, include_schemas=True)


@router.post("", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
def register_topic(body: TopicCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_role("producer"))):
    if db.query(Topic).filter(Topic.name == body.name).first():
        raise HTTPException(status.HTTP_409_CONFLICT, f"topic '{body.name}' already exists")
    t = Topic(name=body.name, description=body.description,
              owner_team=body.owner_team, created_by=user.username)
    t.schemas.append(SchemaVersion(
        version=1,
        definition=body.schema_definition.model_dump_json(),
        created_by=user.username,
    ))
    db.add(t)
    db.commit()
    db.refresh(t)
    cache.invalidate("topics:all")
    kafka_client.create_topic(t.name)
    log.info("topic registered name=%s by=%s", t.name, user.username)
    return _topic_out(t, include_schemas=True)


@router.post("/{name}/schema/check", response_model=CompatibilityResult)
def check_schema(name: str, body: SchemaProposal, db: Session = Depends(get_db),
                 _: User = Depends(current_user)):
    t = db.query(Topic).filter(Topic.name == name).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"topic '{name}' not found")
    latest = max(t.schemas, key=lambda s: s.version)
    old = SchemaDefinition(**json.loads(latest.definition))
    breaking, safe = check_backward(old, body.schema_definition)
    return CompatibilityResult(compatible=not breaking,
                               breaking_changes=breaking, safe_changes=safe)


@router.post("/{name}/schema", response_model=TopicOut)
def evolve_schema(name: str, body: SchemaProposal, db: Session = Depends(get_db),
                  user: User = Depends(require_role("producer"))):
    t = db.query(Topic).filter(Topic.name == name).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"topic '{name}' not found")
    latest = max(t.schemas, key=lambda s: s.version)
    old = SchemaDefinition(**json.loads(latest.definition))
    breaking, _ = check_backward(old, body.schema_definition)
    if breaking:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"message": "schema is not backward-compatible", "breaking_changes": breaking},
        )
    t.schemas.append(SchemaVersion(
        version=latest.version + 1,
        definition=body.schema_definition.model_dump_json(),
        created_by=user.username,
    ))
    db.commit()
    db.refresh(t)
    cache.invalidate("topics:all")
    log.info("schema evolved topic=%s v%d by=%s", name, latest.version + 1, user.username)
    return _topic_out(t, include_schemas=True)


@router.post("/{name}/preview")
def preview_payloads(name: str, body: PreviewRequest, db: Session = Depends(get_db),
                     _: User = Depends(current_user)):
    t = db.query(Topic).filter(Topic.name == name).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"topic '{name}' not found")
    latest = max(t.schemas, key=lambda s: s.version)
    return preview(t.name, latest.definition, body.sample_payloads)
