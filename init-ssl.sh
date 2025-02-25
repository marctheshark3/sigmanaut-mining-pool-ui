#!/bin/bash

# Initialize SSL certificates for production deployment
# This script helps with the initial setup of SSL certificates

set -e

# Check if DOMAIN_NAME is set
if [ -z "$DOMAIN_NAME" ]; then
  echo "Error: DOMAIN_NAME environment variable is not set"
  echo "Please set it with: export DOMAIN_NAME=your-domain.com"
  exit 1
fi

# Check if EMAIL_FOR_SSL is set
if [ -z "$EMAIL_FOR_SSL" ]; then
  echo "Error: EMAIL_FOR_SSL environment variable is not set"
  echo "Please set it with: export EMAIL_FOR_SSL=your-email@example.com"
  exit 1
fi

echo "Starting SSL initialization for $DOMAIN_NAME"
echo "Using email: $EMAIL_FOR_SSL"

# Create directories if they don't exist
mkdir -p ./data/certbot/conf
mkdir -p ./data/certbot/www

# Start nginx for initial certificate validation
echo "Starting nginx for initial validation..."
docker-compose up -d nginx

# Wait for nginx to start
echo "Waiting for nginx to start..."
sleep 5

# Request initial certificates
echo "Requesting initial SSL certificates..."
docker-compose run --rm certbot \
  certonly --webroot --webroot-path=/var/www/certbot \
  --email $EMAIL_FOR_SSL --agree-tos --no-eff-email \
  --force-renewal -d $DOMAIN_NAME

# Reload nginx to apply SSL configuration
echo "Reloading nginx to apply SSL configuration..."
docker-compose exec nginx nginx -s reload

echo "SSL initialization complete for $DOMAIN_NAME"
echo "You can now start your full stack with: docker-compose up -d" 