# 1. Chọn Base Image
FROM nginx@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d

# 2. Thông tin người maintain
LABEL maintainer="yoirk"

# 3. Vá lỗ hổng bảo mật (CVE) & Xóa config mặc định
# Thêm lệnh apk upgrade để update libpng, libxml2 và các gói khác
RUN apk upgrade --no-cache && \
    rm /etc/nginx/conf.d/default.conf

# 4. Copy file config vào trong Image
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 5. Copy mã nguồn Web vào trong Image
COPY html /usr/share/nginx/html

# 6. Phân quyền lại cho user nginx (UID 101)
RUN chown -R 101:101 /usr/share/nginx/html && \
    chown -R 101:101 /etc/nginx/conf.d/default.conf

# 7. Expose port
EXPOSE 80 443

# 8. Start Nginx
CMD ["nginx", "-g", "daemon off;"]