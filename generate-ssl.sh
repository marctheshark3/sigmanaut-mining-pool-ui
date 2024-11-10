#!/bin/bash

# Configuration
DOMAINS=("ergominers.com" "mint.ergominers.com")
EMAIL="marctheshark333@gmail.com"
CERTBOT_PATH="/usr/bin/certbot"
NGINX_PATH="/etc/nginx"
SSL_PATH="/etc/nginx/ssl"

# Function to generate certificates with enhanced checks
generate_certificates() {
    local domain_args=""
    for domain in "${DOMAINS[@]}"; do
        domain_args="$domain_args -d $domain"
    done
    
    echo "Stopping Nginx..."
    sudo systemctl stop nginx
    
    echo "Cleaning up any existing certificates..."
    sudo rm -rf /etc/letsencrypt/live/ergominers.com*
    sudo rm -rf /etc/letsencrypt/archive/ergominers.com*
    sudo rm -rf /etc/letsencrypt/renewal/ergominers.com*
    sudo rm -rf "$SSL_PATH"/*
    
    echo "Generating new certificates..."
    sudo "$CERTBOT_PATH" certonly \
        --standalone \
        --preferred-challenges http \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --force-renewal \
        $domain_args
        
    echo "Copying certificates with full chain..."
    sudo mkdir -p "$SSL_PATH"
    sudo cp /etc/letsencrypt/live/ergominers.com/fullchain.pem "$SSL_PATH/fullchain.pem"
    sudo cp /etc/letsencrypt/live/ergominers.com/privkey.pem "$SSL_PATH/privkey.pem"
    
    # Also copy the chain file separately
    sudo cp /etc/letsencrypt/live/ergominers.com/chain.pem "$SSL_PATH/chain.pem"
    
    echo "Setting proper permissions..."
    sudo chmod 644 "$SSL_PATH/fullchain.pem"
    sudo chmod 644 "$SSL_PATH/chain.pem"
    sudo chmod 600 "$SSL_PATH/privkey.pem"
    
    echo "Starting Nginx..."
    sudo systemctl start nginx
}

# Main execution
main() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "Please run as root"
        exit 1
    fi
    
    # Install certbot if not present
    if ! command -v certbot >/dev/null 2>&1; then
        echo "Installing certbot..."
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
    
    generate_certificates
    
    # Verify the installation
    echo "Verifying certificate installation..."
    openssl verify -CAfile "$SSL_PATH/chain.pem" "$SSL_PATH/fullchain.pem"
    
    echo "Process completed! Testing nginx configuration..."
    nginx -t
}

main