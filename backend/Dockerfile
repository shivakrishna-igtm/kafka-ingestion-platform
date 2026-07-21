# ---- build stage: compile gRPC stubs for the preview client ----
FROM python:3.12-slim AS build
WORKDIR /build
RUN pip install --no-cache-dir grpcio-tools==1.64.1
COPY preview-service/proto/preview.proto proto/
RUN python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/preview.proto

# ---- runtime ----
FROM python:3.12-slim
WORKDIR /api
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt confluent-kafka==2.4.0
COPY backend/app/ app/
COPY preview-service/snowflake_mapper.py /preview-service/snowflake_mapper.py
COPY --from=build /build/preview_pb2.py /build/preview_pb2_grpc.py ./
EXPOSE 8000
HEALTHCHECK --interval=15s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
