FROM nginx:stable-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl ssl-cert \
    && openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout /etc/ssl/private/ssl-cert-snakeoil.key \
        -out /etc/ssl/certs/ssl-cert-snakeoil.pem \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    && chown root:ssl-cert /etc/ssl/private/ssl-cert-snakeoil.key \
    && chmod 640 /etc/ssl/private/ssl-cert-snakeoil.key \
    && usermod -aG ssl-cert nginx \
    && rm -rf /var/lib/apt/lists/*

COPY default.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
