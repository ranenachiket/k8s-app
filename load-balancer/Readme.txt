Nginx - Load Balancer (Raspi-5)

Install and start Nginx server:
sudo apt update
sudo apt install -y nginx

sudo systemctl enable nginx
sudo systemctl start nginx

Verify: http://192.168.87.32/ (Nginx webpage)

=====================================
Configure NGINX as a Load Balancer for Kong
=====================================
nrane@pi5-load-balancer:~$ cat /etc/nginx/conf.d/kong.conf
upstream kong_gateway {
    server 192.168.87.50:30080 max_fails=3 fail_timeout=10s;
    server 192.168.87.51:30080 max_fails=3 fail_timeout=10s;
    server 192.168.87.52:30080 max_fails=3 fail_timeout=10s;
    keepalive 32;
}

server {
    listen 80;
    server_name kong.local;

    location / {
        proxy_pass http://kong_gateway/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "";

        # Important timeout and buffering fixes
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        send_timeout 30s;

        proxy_buffering on;
        proxy_buffers 8 512k;
        proxy_busy_buffers_size 512k;
        proxy_max_temp_file_size 0;
    }

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
}
==================
Test the configuration:
==================
nrane@load-balancer:~ $ sudo nginx -t && sudo systemctl reload nginx
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful

Verify:http://kong.local/  (Should show the Kong)


================ Load balancer nginx logs ==========================

tail -f /var/log/nginx/access.log
tail -f  /var/log/nginx/errorlog