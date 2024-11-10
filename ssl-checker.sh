#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check certificate paths
check_cert_paths() {
    echo "Checking certificate paths..."
    
    # Check Let's Encrypt live directory
    if [ -d "/etc/letsencrypt/live/ergominers.com" ]; then
        echo -e "${GREEN}Let's Encrypt directory exists${NC}"
        ls -l /etc/letsencrypt/live/ergominers.com
    else
        echo -e "${RED}Let's Encrypt directory not found!${NC}"
    fi
    
    # Check Nginx SSL directory
    if [ -d "/etc/nginx/ssl" ]; then
        echo -e "${GREEN}Nginx SSL directory exists${NC}"
        ls -l /etc/nginx/ssl
    else
        echo -e "${RED}Nginx SSL directory not found!${NC}"
    fi
}

# Function to verify certificate validity
check_cert_validity() {
    echo -e "\nChecking certificate validity..."
    
    if [ -f "/etc/nginx/ssl/fullchain.pem" ]; then
        echo -e "\nCertificate details:"
        openssl x509 -in /etc/nginx/ssl/fullchain.pem -text -noout | grep -E "Subject:|Issuer:|Not Before:|Not After:"
    else
        echo -e "${RED}Certificate file not found in Nginx SSL directory!${NC}"
    fi
}

# Function to test Nginx configuration
check_nginx_config() {
    echo -e "\nChecking Nginx configuration..."
    nginx -t
}

# Main execution
main() {
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}Please run as root${NC}"
        exit 1
    fi
    
    check_cert_paths
    check_cert_validity
    check_nginx_config
    
    echo -e "\nChecking domain SSL connection..."
    echo -e "Testing connection to ergominers.com..."
    curl -vI https://ergominers.com 2>&1 | grep "SSL connection"
}

main