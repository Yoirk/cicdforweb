# Chọn Base Image    
FROM python:3.10-alpine@sha256:396410c739456800dd74a886783c6b77ba1121e6ca137463414b905f3a65df95

# Setup môi trường
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài đặt Litestream
COPY --from=litestream/litestream:0.3.13 /usr/local/bin/litestream /usr/local/bin/litestream

# Tạo User & Thư mục Data TRƯỚC
RUN mkdir /data && \
    adduser -D -u 1001 pythonuser && \
    chown -R 1001:1001 /data

# Copy dependency
COPY --chown=1001:1001 requirements.txt .

# Cập nhật pip và cài đặt gói
# pip install vẫn chạy dưới quyền root để cài vào site-packages toàn cục
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --upgrade --force-reinstall "jaraco.context>=6.1.0"

# giúp giảm dung lượng vì không cần chạy chown -R /app sau đó
COPY --chown=1001:1001 main.py .

# Copy file cấu hình Litestream
COPY litestream.yml /etc/litestream.yml

# Debug dependency
RUN pip install pipdeptree && \
    echo "=== CHECK VERSION ===" && \
    pip show jaraco.context || true && \
    echo "=== CHECK DEPENDENCY ===" && \
    pipdeptree --reverse --packages jaraco.context || true

# Chuyển sang user 1001 để chạy app an toàn
USER 1001

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["litestream", "replicate", "-exec", "uvicorn main:app --host 0.0.0.0 --port 8000"]