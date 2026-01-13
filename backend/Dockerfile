FROM python:3.10-alpine

# Setup môi trường
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài dependency
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY main.py .

# Tạo thư mục data và user non-root (UID 1001)
RUN mkdir /data && \
    adduser -D -u 1001 pythonuser && \
    chown -R 1001:1001 /app /data

USER 1001

# Chạy app ở port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]