# Sigmanauts Mining Pool Dashboard

[![Telegram Group](https://img.shields.io/badge/Telegram-Join%20Chat-blue.svg)](https://t.me/sig_mining)

A comprehensive dashboard for monitoring and managing your Ergo mining operations through the Sigmanauts Mining Pool.

## 📋 Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Pool Connection Guide](#pool-connection-guide)
- [Domain and SSL Configuration](#domain-and-ssl-configuration)
- [Contributing](#contributing)
- [Support](#support)

## ✨ Features
- Real-time mining statistics and monitoring
- User-friendly dashboard interface
- Secure pool connection options
- Support for multiple mining software
- Automatic SSL certificate management
- Docker-based deployment

## 🚀 Quick Start

1. Start the dashboard:
```bash
docker compose up -d
```

2. Access the dashboard at: http://localhost:8050/
3. Enter your wallet address in the input tab

## 💻 Installation

### Prerequisites
- Docker and Docker Compose
- Git (for development)

### Using Pre-built Docker Image
```bash
# Stop any running instance
docker compose down

# Pull latest version
docker compose pull

# Start the dashboard
docker compose up -d
```

### Building from Source
```bash
# Clone the repository
git clone [repository-url]

# Navigate to project directory
cd sigma-dashboard

# Build and start
docker compose up --build -d
```

## 🔗 Pool Connection Guide

### Available Ports

Choose the appropriate port based on your hashrate and TLS requirements:

| Port | Hashrate | TLS | Description |
|------|----------|-----|-------------|
| 3052 | < 10GH/s | No  | Standard connection |
| 3053 | > 10GH/s | No  | High-performance connection |
| 3054 | < 10GH/s | Yes | Secure standard connection |
| 3055 | > 10GH/s | Yes | Secure high-performance connection |

**Pool URL:** 65.108.57.232

### Mining Software Configuration

#### HiveOS
1. Create a new Flight Sheet
2. Set Pool to "configure in miner"
3. Set Pool URL: `65.108.57.232:3052` (adjust port as needed)

#### MMPOS
1. Navigate to Management and create a new pool
2. Hostname: `65.108.57.232`
3. Port: `3052` (adjust as needed)

#### Linux/Windows (lolMiner Example)
```bash
POOL=65.108.57.232:3052
WALLET=your_wallet_address

./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
while [ $? -eq 42 ]; do
    sleep 10s
    ./lolMiner --algo AUTOLYKOS2 --pool $POOL --user $WALLET $@
done
```

## 🔒 Domain and SSL Configuration

### Environment Setup
Create a `.env` file with:
```env
# Domain Configuration
DOMAIN_NAME=localhost  # Or your domain (e.g., ergominers.com)
ENABLE_HTTPS=false    # Set true for production
EMAIL_FOR_SSL=your-email@example.com  # For Let's Encrypt
```

### Development Environment
```env
DOMAIN_NAME=localhost
ENABLE_HTTPS=false
```

### Production Environment
1. Update `.env`:
```env
DOMAIN_NAME=your-domain.com
ENABLE_HTTPS=true
EMAIL_FOR_SSL=your-email@example.com
```

2. Configure DNS for your domain
3. Initialize SSL:
```bash
docker-compose exec nginx /scripts/init-ssl.sh
```

### SSL Certificate Management
- Automatic certificate management via Certbot
- 90-day certificates with automatic renewal
- Renewal checks every 12 hours
- Certificates stored in `certbot_conf` Docker volume

## 👥 Contributing
We welcome contributions! Please feel free to submit pull requests.

## 💝 Support

If you find this tool helpful, consider supporting its development:

ERGO ADDRESS: `9f2nrcC2NHsx96RmN52g3GVV3kXkZQPkNG8M6SVpSRqdmaxVtGv`

## 📞 Contact

Join our [Telegram group](https://t.me/sig_mining) for support and updates!
