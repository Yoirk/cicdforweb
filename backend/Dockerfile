# [Stage 1] Builder: Compile Litestream với latest Go để fix CVEs
FROM golang:1.25-alpine@sha256:ac09a5f469f307e5da71e766b0bd59c9c49ea460a528cc3e6686513d64a6f1fb AS builder

WORKDIR /build

# Cài đặt git và build-base (gcc)
RUN apk add --no-cache git build-base

# Clone source code v0.3.13
RUN git clone --depth 1 --branch v0.3.13 https://github.com/benbjohnson/litestream.git .

# Tải về các dependency mới nhất để fix CVEs
RUN go get golang.org/x/crypto@latest \
           golang.org/x/net@latest \
           golang.org/x/oauth2@latest \
           google.golang.org/grpc@latest \
           github.com/mattn/go-sqlite3@latest && \
    go mod tidy

# Build binary tĩnh với CGO enabled
# -tags osusergo,netgo: Dùng network stack của Go
# -ldflags '-extldflags "-static"': Ép static link thư viện C (sqlite) vào binary
RUN CGO_ENABLED=1 go build -tags osusergo,netgo -ldflags '-extldflags "-static" -s -w' -o /litestream ./cmd/litestream

# [Stage 2] Final Image: Run App
FROM python:3.10-alpine@sha256:396410c739456800dd74a886783c6b77ba1121e6ca137463414b905f3a65df95

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy binary sạch từ Stage 1
COPY --from=builder /litestream /usr/local/bin/litestream

# Tạo User & Folder
RUN mkdir /data && \
    adduser -D -u 1001 pythonuser && \
    chown -R 1001:1001 /data

COPY --chown=1001:1001 requirements.txt .

# Cài đặt dependency
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade --force-reinstall "jaraco.context>=6.1.0"

COPY --chown=1001:1001 main.py .
COPY litestream.yml /etc/litestream.yml

# Debug check
RUN pip install pipdeptree && \
    pip show jaraco.context || true && \
    pipdeptree --reverse --packages jaraco.context || true

USER 1001

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["litestream", "replicate", "-exec", "uvicorn main:app --host 0.0.0.0 --port 8000"]