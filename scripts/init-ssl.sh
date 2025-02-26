#!/bin/bash

# Check if domain name is provided
if [ -z "$DOMAIN_NAME" ]; then
    echo "Error: DOMAIN_NAME environment variable is not set"
    exit 1
fi

if [ -z "$EMAIL_FOR_SSL" ]; then
    echo "Error: EMAIL_FOR_SSL environment variable is not set"
    exit 1
fi

# Create temporary nginx config for SSL setup
cat > /etc/nginx/conf.d/default.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

# Reload nginx to apply temporary config
nginx -s reload

# Request the SSL certificate
certbot certonly --webroot \
  --webroot-path /var/www/certbot \
  --email $EMAIL_FOR_SSL \
  --agree-tos \
  --no-eff-email \
  --force-renewal \
  -d $DOMAIN_NAME

# Reload nginx again to use the new certificates
nginx -s reload 