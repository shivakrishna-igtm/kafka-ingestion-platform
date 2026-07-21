"""Maps JSON payloads to Snowflake table shape.

Models the staged-loading path: payloads land in a stage as files,
then COPY INTO loads them into the target table. This module answers
the question "what will my Kafka payload look like as Snowflake rows?"
"""
from __future__ import annotations

import json
import re
from typing import Any

ISO_TS = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


def infer_snowflake_type(value: Any) -> str:
    """JSON value -> Snowflake type."""
    if value is None:
        return "VARCHAR"           # unknown until a non-null arrives
    if isinstance(value, bool):    # bool before int: bool is a subclass of int
        return "BOOLEAN"
    if isinstance(value, int):
        return "NUMBER(38,0)"
    if isinstance(value, float):
        return "FLOAT"
    if isinstance(value, str):
        return "TIMESTAMP_NTZ" if ISO_TS.match(value) else "VARCHAR"
    if isinstance(value, (dict, list)):
        return "VARIANT"           # semi-structured lands as VARIANT
    return "VARCHAR"


# registry field type -> Snowflake type (the registered schema contract)
REGISTRY_TYPE_MAP = {
    "string": "VARCHAR",
    "int": "NUMBER(38,0)",
    "long": "NUMBER(38,0)",
    "float": "FLOAT",
    "double": "FLOAT",
    "boolean": "BOOLEAN",
    "timestamp": "TIMESTAMP_NTZ",
    "object": "VARIANT",
    "array": "VARIANT",
}


def column_name(field: str) -> str:
    """Snowflake unquoted identifiers resolve to uppercase."""
    return re.sub(r"[^A-Za-z0-9_]", "_", field).upper()


def coerce(value: Any, sf_type: str) -> tuple[str, str | None]:
    """Coerce a JSON value to its Snowflake column representation.

    Returns (display_value, warning_or_none).
    """
    if value is None:
        return "NULL", None
    if sf_type == "BOOLEAN":
        if isinstance(value, bool):
            return str(value).upper(), None
        return str(bool(value)).upper(), f"coerced {value!r} to BOOLEAN"
    if sf_type.startswith("NUMBER"):
        if isinstance(value, bool):
            return ("1" if value else "0"), "coerced BOOLEAN to NUMBER"
        try:
            coerced = str(int(value))
            warn = None if isinstance(value, int) else f"coerced {value!r} to NUMBER"
            return coerced, warn
        except (TypeError, ValueError):
            return "NULL", f"could not coerce {value!r} to NUMBER - landing NULL"
    if sf_type == "FLOAT":
        try:
            return str(float(value)), None
        except (TypeError, ValueError):
            return "NULL", f"could not coerce {value!r} to FLOAT - landing NULL"
    if sf_type == "TIMESTAMP_NTZ":
        if isinstance(value, str) and ISO_TS.match(value):
            return value.replace("T", " ").rstrip("Z"), None
        return "NULL", f"value {value!r} is not an ISO timestamp - landing NULL"
    if sf_type == "VARIANT":
        return json.dumps(value, separators=(",", ":")), None
    return str(value), None


def build_preview(topic_name: str, registered_schema: dict | None,
                  payloads: list[dict]) -> dict:
    """Produce columns, coerced rows, DDL, COPY INTO, and warnings."""
    warnings: list[str] = []

    # 1. Start from the registered contract if present
    columns: dict[str, dict] = {}
    if registered_schema:
        for f in registered_schema.get("fields", []):
            sf = REGISTRY_TYPE_MAP.get(f.get("type", "string"), "VARCHAR")
            columns[column_name(f["name"])] = {
                "source": f["name"],
                "type": sf,
                "nullable": not f.get("required", False),
            }

    # 2. Fold in what the sample payloads actually contain
    for i, payload in enumerate(payloads):
        for key, value in payload.items():
            col = column_name(key)
            inferred = infer_snowflake_type(value)
            if col not in columns:
                columns[col] = {"source": key, "type": inferred, "nullable": True}
                if registered_schema:
                    warnings.append(
                        f"payload #{i+1}: field '{key}' is not in the registered "
                        f"schema - it would land as an extra column {col} {inferred}"
                    )
            else:
                expected = columns[col]["type"]
                if (value is not None and inferred not in (expected, "VARCHAR")
                        and expected != "VARIANT"):
                    warnings.append(
                        f"payload #{i+1}: field '{key}' arrived as {inferred} "
                        f"but the contract says {expected}"
                    )

    # 3. Coerce each payload into rows
    rows = []
    for i, payload in enumerate(payloads):
        row = {}
        for col, meta in columns.items():
            raw = payload.get(meta["source"])
            display, warn = coerce(raw, meta["type"])
            if raw is None and not meta["nullable"]:
                warnings.append(
                    f"payload #{i+1}: required field '{meta['source']}' is missing "
                    f"- COPY INTO would reject this record under NOT NULL"
                )
            if warn:
                warnings.append(f"payload #{i+1}: {warn}")
            row[col] = display
        rows.append(row)

    # 4. DDL + staged COPY INTO
    table = column_name(topic_name)
    col_lines = ",\n  ".join(
        f"{c} {m['type']}" + ("" if m["nullable"] else " NOT NULL")
        for c, m in columns.items()
    )
    ddl = f"CREATE TABLE IF NOT EXISTS RAW.{table} (\n  {col_lines}\n);"
    copy_sql = (
        f"COPY INTO RAW.{table}\n"
        f"FROM @KAFKA_STAGE/{topic_name}/\n"
        f"FILE_FORMAT = (TYPE = 'JSON' STRIP_OUTER_ARRAY = TRUE)\n"
        f"MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE\n"
        f"ON_ERROR = 'SKIP_FILE';"
    )

    return {
        "columns": [
            {"name": c, "snowflake_type": m["type"], "nullable": m["nullable"]}
            for c, m in columns.items()
        ],
        "rows": rows,
        "warnings": warnings,
        "create_table_ddl": ddl,
        "copy_into_sql": copy_sql,
    }
