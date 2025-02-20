#!/bin/bash

# Help function
show_help() {
    echo "Usage: ./start.sh [OPTIONS]"
    echo "Start the Sigmanaut Mining Pool services"
    echo ""
    echo "Options:"
    echo "  --with-nginx    Start services with nginx reverse proxy"
    echo "  --build        Force rebuild of containers"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start.sh                   # Start core services only"
    echo "  ./start.sh --with-nginx      # Start with nginx"
    echo "  ./start.sh --with-nginx --build  # Start with nginx and force rebuild"
}

# Default values
WITH_NGINX=false
BUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-nginx)
            WITH_NGINX=true
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Stop any running containers
echo "Stopping existing containers..."
docker compose -f docker-compose.base.yaml down
if [ "$WITH_NGINX" = true ]; then
    docker compose -f docker-compose.nginx.yaml down
fi

# Build and start containers
if [ "$WITH_NGINX" = true ]; then
    echo "Starting services with nginx..."
    if [ "$BUILD" = true ]; then
        docker compose -f docker-compose.base.yaml -f docker-compose.nginx.yaml up --build -d
    else
        docker compose -f docker-compose.base.yaml -f docker-compose.nginx.yaml up -d
    fi
else
    echo "Starting core services without nginx..."
    if [ "$BUILD" = true ]; then
        docker compose -f docker-compose.base.yaml up --build -d
    else
        docker compose -f docker-compose.base.yaml up -d
    fi
fi

# Show running containers
echo -e "\nRunning containers:"
docker compose -f docker-compose.base.yaml ps 