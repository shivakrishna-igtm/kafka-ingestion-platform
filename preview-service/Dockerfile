# ---- build stage: compile proto stubs ----
FROM python:3.12-slim AS build
WORKDIR /svc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proto/ proto/
RUN python -m grpc_tools.protoc -Iproto --python_out=. --grpc_python_out=. proto/preview.proto

# ---- runtime stage: slim image, no build tooling ----
FROM python:3.12-slim
WORKDIR /svc
RUN pip install --no-cache-dir grpcio==1.64.1 "protobuf>=4.25,<6"
COPY --from=build /svc/preview_pb2.py /svc/preview_pb2_grpc.py ./
COPY server.py snowflake_mapper.py ./
EXPOSE 50051
CMD ["python", "server.py"]
