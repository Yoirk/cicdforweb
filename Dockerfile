# 1. Chọn Base Image
FROM nginx:1.29.5-alpine@sha256:05fcc6f6c80dc65c0f241f250677aad26e0962d118abaa65a513796862ff915d

# 2. Thông tin người maintain
LABEL maintainer="yoirk"

# 3. Vá lỗ hổng bảo mật (CVE) & Xóa config mặc định
RUN apk upgrade --no-cache && \
    rm /etc/nginx/conf.d/default.conf

# 4. Copy config & source code 
# Dùng --chown để set quyền ngay khi copy, không tạo thêm layer thừa
COPY --chown=101:101 nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 html /usr/share/nginx/html

# 5. Expose port
EXPOSE 80 443

# 6. Chạy với user non-root 
USER 101

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:80/ || exit 1
  
# 7. Start Nginx
CMD ["nginx", "-g", "daemon off;"]