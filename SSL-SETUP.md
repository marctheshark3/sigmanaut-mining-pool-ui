# SSL/HTTPS Setup for Production

This guide explains how to set up SSL/HTTPS for your Sigma Dashboard in a production environment.

## Prerequisites

1. A domain name pointing to your server IP address
2. A server with Docker and Docker Compose installed
3. Ports 80 and 443 open on your server firewall

## SSL/HTTPS Setup Steps

### 1. Set Environment Variables

Set the required environment variables in a `.env` file in the project root:

```bash
# .env file
DOMAIN_NAME=your-domain.com
EMAIL_FOR_SSL=your-email@example.com
```

### 2. Run the SSL Initialization Script

Run the included initialization script to set up SSL certificates:

```bash
./init-ssl.sh
```

This script will:
- Verify the required environment variables are set
- Start Nginx to handle the domain validation
- Run Certbot to obtain the initial SSL certificates
- Reload Nginx to apply the SSL configuration

### 3. Start the Full Stack

Once SSL is initialized, you can start the full stack:

```bash
docker-compose up -d
```

### 4. Test SSL/HTTPS

Visit your domain with HTTPS to verify it's working:

```
https://your-domain.com
```

## SSL Certificate Renewal

The Certbot service in Docker Compose is configured to automatically renew your SSL certificates before they expire. This happens every 12 hours (only performing renewal when necessary).

## Troubleshooting

### SSL Certificate Issues

If you're having issues with SSL certificates:

1. Check certificate status:
```bash
docker-compose exec certbot certbot certificates
```

2. Force certificate renewal:
```bash
docker-compose exec certbot certbot renew --force-renewal
```

3. Check Nginx logs:
```bash
docker-compose logs nginx
```

4. Check Certbot logs:
```bash
docker-compose logs certbot
```

### SSL Configuration

The SSL configuration is in `nginx/nginx.conf.template`. The key settings are:
- TLS protocols: TLSv1.2 and TLSv1.3
- Strong ciphers for better security
- OCSP Stapling enabled
- HTTP Strict Transport Security (HSTS) enabled
- Additional security headers included

## Manual Certificate Management

If you need to manually manage certificates:

1. Create a certificate:
```bash
docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot \
  --email your-email@example.com --agree-tos --no-eff-email \
  --force-renewal -d your-domain.com
```

2. Reload Nginx after certificate changes:
```bash
docker-compose exec nginx nginx -s reload
``` 