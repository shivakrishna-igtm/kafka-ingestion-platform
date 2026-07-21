"""Client for the gRPC preview service.

When PREVIEW_GRPC_TARGET is unset (tests, minimal local runs) the same
mapper logic runs in-process, so behavior is identical either way.
"""
import json
import sys
from pathlib import Path

from .config import settings


def _in_process(topic_name: str, schema_json: str, payloads: list[dict]) -> dict:
    svc_dir = Path(__file__).resolve().parents[2] / "preview-service"
    if str(svc_dir) not in sys.path:
        sys.path.insert(0, str(svc_dir))
    from snowflake_mapper import build_preview  # noqa: PLC0415
    schema = json.loads(schema_json) if schema_json else None
    return build_preview(topic_name, schema, payloads)


def _over_grpc(topic_name: str, schema_json: str, payloads: list[dict]) -> dict:
    import grpc  # noqa: PLC0415
    import preview_pb2  # noqa: PLC0415
    import preview_pb2_grpc  # noqa: PLC0415

    with grpc.insecure_channel(settings.preview_grpc_target) as channel:
        stub = preview_pb2_grpc.PreviewServiceStub(channel)
        resp = stub.PreviewPayload(
            preview_pb2.PreviewRequest(
                topic_name=topic_name,
                registered_schema_json=schema_json,
                sample_payloads=[json.dumps(p) for p in payloads],
            ),
            timeout=10,
        )
    return {
        "columns": [
            {"name": c.name, "snowflake_type": c.snowflake_type, "nullable": c.nullable}
            for c in resp.columns
        ],
        "rows": [dict(r.values) for r in resp.rows],
        "warnings": list(resp.warnings),
        "create_table_ddl": resp.create_table_ddl,
        "copy_into_sql": resp.copy_into_sql,
    }


def preview(topic_name: str, schema_json: str, payloads: list[dict]) -> dict:
    if settings.preview_grpc_target:
        return _over_grpc(topic_name, schema_json, payloads)
    return _in_process(topic_name, schema_json, payloads)
