"""Pydantic request/response models."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

FIELD_TYPES = {"string", "int", "long", "float", "double",
               "boolean", "timestamp", "object", "array"}


class FieldDef(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str
    required: bool = False

    @field_validator("type")
    @classmethod
    def known_type(cls, v: str) -> str:
        if v not in FIELD_TYPES:
            raise ValueError(f"unknown field type '{v}'; expected one of {sorted(FIELD_TYPES)}")
        return v


class SchemaDefinition(BaseModel):
    fields: list[FieldDef] = Field(min_length=1)


class TopicCreate(BaseModel):
    name: str = Field(min_length=3, max_length=128, pattern=r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$")
    description: str = ""
    owner_team: str = ""
    schema_definition: SchemaDefinition


class SchemaProposal(BaseModel):
    schema_definition: SchemaDefinition


class SchemaVersionOut(BaseModel):
    version: int
    definition: SchemaDefinition
    created_by: str
    created_at: datetime


class TopicOut(BaseModel):
    id: int
    name: str
    description: str
    owner_team: str
    created_by: str
    created_at: datetime
    latest_version: int
    schemas: list[SchemaVersionOut] = []


class CompatibilityResult(BaseModel):
    compatible: bool
    mode: Literal["BACKWARD"] = "BACKWARD"
    breaking_changes: list[str] = []
    safe_changes: list[str] = []


class PreviewRequest(BaseModel):
    sample_payloads: list[dict] = Field(min_length=1, max_length=25)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
