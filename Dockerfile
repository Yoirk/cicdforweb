# 1. Chọn Base Image
FROM nginx@sha256:1eadbb07820339e8bbfed18c771691970baee292ec4ab2558f1453d26153e22d

# 2. Thông tin người maintain
LABEL maintainer="yoirk"

# 3. Xóa config mặc định của Nginx để tránh xung đột
RUN rm /etc/nginx/conf.d/default.conf

# 4. Copy file config vào trong Image
# (Lưu ý: đường dẫn nguồn là tương đối so với file Dockerfile)
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 5. Copy mã nguồn Web vào trong Image
COPY html /usr/share/nginx/html

# 6. Phân quyền lại cho user nginx (UID 101) sở hữu các file này
# Để đảm bảo user 101 đọc được, dù chạy ở đâu
RUN chown -R 101:101 /usr/share/nginx/html && \
    chown -R 101:101 /etc/nginx/conf.d/default.conf

# 7. Expose port (khai báo tượng trưng)
EXPOSE 80 443

# 8. Start Nginx
CMD ["nginx", "-g", "daemon off;"]