#!/bin/bash

# Configuration
DOMAINS=("ergominers.com" "mint.ergominers.com")
EMAIL="admin@ergominers.com"  # Replace with your email
CERTBOT_PATH="/usr/bin/certbot"
NGINX_PATH="/etc/nginx"
SSL_PATH="/etc/nginx/ssl"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check and install dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
    # Check if certbot is installed
    if ! command_exists certbot; then
        echo -e "${YELLOW}Certbot not found. Installing...${NC}"
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    fi
}

# Function to create required directories
create_directories() {
    echo "Creating required directories..."
    sudo mkdir -p "$SSL_PATH"
    sudo chmod 755 "$SSL_PATH"
}

# Function to check if certificates already exist
check_existing_certs() {
    local domain=$1
    if [ -f "$SSL_PATH/fullchain.pem" ] && [ -f "$SSL_PATH/privkey.pem" ]; then
        echo -e "${YELLOW}Certificates already exist for $domain${NC}"
        return 0
    fi
    return 1
}

# Function to generate certificates
generate_certificates() {
    local domain_args=""
    for domain in "${DOMAINS[@]}"; do
        domain_args="$domain_args -d $domain"
    done
    
    echo "Generating certificates for domains: ${DOMAINS[*]}"
    
    # Stop nginx temporarily if it's running
    if systemctl is-active --quiet nginx; then
        sudo systemctl stop nginx
    fi
    
    # Generate certificates
    sudo "$CERTBOT_PATH" certonly \
        --standalone \
        --preferred-challenges http \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        $domain_args
        
    # Copy certificates to nginx ssl directory
    sudo cp /etc/letsencrypt/live/"${DOMAINS[0]}"/fullchain.pem "$SSL_PATH/fullchain.pem"
    sudo cp /etc/letsencrypt/live/"${DOMAINS[0]}"/privkey.pem "$SSL_PATH/privkey.pem"
    
    # Set proper permissions
    sudo chmod 644 "$SSL_PATH/fullchain.pem"
    sudo chmod 600 "$SSL_PATH/privkey.pem"
    
    # Start nginx
    sudo systemctl start nginx
}

# Function to setup auto-renewal
setup_auto_renewal() {
    echo "Setting up auto-renewal..."
    
    # Create renewal script
    cat << 'EOF' | sudo tee /etc/cron.monthly/ssl-renewal.sh
#!/bin/bash
certbot renew --quiet --no-self-upgrade
cp /etc/letsencrypt/live/ergominers.com/fullchain.pem /etc/nginx/ssl/fullchain.pem
cp /etc/letsencrypt/live/ergominers.com/privkey.pem /etc/nginx/ssl/privkey.pem
systemctl reload nginx
EOF
    
    # Make it executable
    sudo chmod +x /etc/cron.monthly/ssl-renewal.sh
}

# Main execution
main() {
    echo "Starting SSL certificate generation process..."
    
    # Check if script is run as root
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}Please run as root${NC}"
        exit 1
    }
    
    check_dependencies
    create_directories
    
    if ! check_existing_certs "${DOMAINS[0]}"; then
        generate_certificates
        setup_auto_renewal
        echo -e "${GREEN}SSL certificates have been successfully generated and installed!${NC}"
    else
        read -p "Certificates already exist. Do you want to regenerate them? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            generate_certificates
            setup_auto_renewal
            echo -e "${GREEN}SSL certificates have been successfully regenerated and installed!${NC}"
        else
            echo -e "${YELLOW}Skipping certificate generation${NC}"
        fi
    fi
    
    echo -e "${GREEN}Process completed!${NC}"
}

main