"""gRPC server exposing Snowflake landing previews."""
import json
import logging
from concurrent import futures

import grpc

import preview_pb2
import preview_pb2_grpc
from snowflake_mapper import build_preview

logging.basicConfig(
    level=logging.INFO,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","svc":"preview","msg":"%(message)s"}',
)
log = logging.getLogger("preview")


class PreviewService(preview_pb2_grpc.PreviewServiceServicer):
    def PreviewPayload(self, request, context):
        log.info("preview requested topic=%s samples=%d",
                 request.topic_name, len(request.sample_payloads))
        try:
            schema = (json.loads(request.registered_schema_json)
                      if request.registered_schema_json else None)
            payloads = []
            for raw in request.sample_payloads:
                obj = json.loads(raw)
                if not isinstance(obj, dict):
                    context.abort(grpc.StatusCode.INVALID_ARGUMENT,
                                  "each sample payload must be a JSON object")
                payloads.append(obj)
        except json.JSONDecodeError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"invalid JSON: {e}")

        result = build_preview(request.topic_name, schema, payloads)
        return preview_pb2.PreviewResponse(
            columns=[preview_pb2.ColumnDef(**c) for c in result["columns"]],
            rows=[preview_pb2.PreviewRow(values=r) for r in result["rows"]],
            warnings=result["warnings"],
            create_table_ddl=result["create_table_ddl"],
            copy_into_sql=result["copy_into_sql"],
        )


def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    preview_pb2_grpc.add_PreviewServiceServicer_to_server(PreviewService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    log.info("preview service listening on :%d", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
