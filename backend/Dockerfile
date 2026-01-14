# 1. Chọn Base Image
FROM python:3.10-alpine

# Setup môi trường
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy dependency
COPY requirements.txt .

# Cập nhật pip và setuptools trước để tránh lỗi dependency cũ
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Cài đặt các gói của dự án
RUN pip install --no-cache-dir -r requirements.txt

# Chạy lệnh này SAU KHI cài requirements để đảm bảo không bị pip tự động downgrade lại
# --force-reinstall: Ép buộc cài lại kể cả khi pip nghĩ là đã có
RUN pip install --no-cache-dir --upgrade --force-reinstall "jaraco.context>=6.1.0"

# Copy code (Làm bước này cuối để tận dụng cache Docker layers)
COPY main.py .

RUN mkdir /data && \
    adduser -D -u 1001 pythonuser && \
    chown -R 1001:1001 /app /data

USER 1001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]