# 1. Chọn Base Image
FROM nginx:1.26-alpine@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d

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

# 7. Start Nginx
CMD ["nginx", "-g", "daemon off;"]