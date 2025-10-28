# WAMems Deployment Guide

## Overview
This guide explains how to deploy the WAMems (WhatsApp-Google Sync) system to a Contabo VPS under evolution.cig.chat.

## Prerequisites

### Server Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name: evolution.cig.chat
- SSL certificate (Let's Encrypt)
- Minimum 2GB RAM, 20GB storage

### DNS Configuration
Before deployment, configure these DNS records:
- A record: `evolution.cig.chat` → VPS IP address
- Optional: CNAME `api.evolution.cig.chat` → `evolution.cig.chat`

## Quick Deployment

### 1. Clone and Setup
```bash
# Clone the repository
git clone <repository-url> wamems
cd wamems

# Make scripts executable
chmod +x scripts/*.sh
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.production.example .env.production

# Edit configuration
nano .env.production
```

**Important**: Update these values in `.env.production`:
- `SECRET_KEY`: Generate a secure random key
- `ADMIN_PASSWORD_HASH`: Generate password hash for admin@cig.chat
- `DOMAIN`: evolution.cig.chat

### 3. Generate Admin Password Hash
```bash
# Install Python dependencies
pip install cryptography

# Generate password hash
python3 -c "
from backend.auth_manager import AuthManager
import os
password = input('Enter admin password: ')
auth = AuthManager('temp', 'admin@cig.chat', 'temp')
hash_value = auth.hash_password(password)
print(f'ADMIN_PASSWORD_HASH={hash_value}')
"
```

### 4. Deploy Application
```bash
# Run deployment script
./scripts/deploy.sh
```

### 5. Setup SSL Certificate
```bash
# Setup SSL (run after DNS is configured)
./scripts/setup-ssl.sh
```

## Manual Deployment Steps

### 1. Install Docker
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configure Nginx
The nginx configuration is already included in `nginx/evolution.cig.chat.conf`.

### 3. Start Services
```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps
```

### 4. Verify Deployment
```bash
# Check logs
docker-compose logs -f

# Test endpoints
curl https://evolution.cig.chat/health
curl https://evolution.cig.chat/api/status
```

## Post-Deployment Configuration

### 1. Admin Login
- URL: https://evolution.cig.chat
- Email: admin@cig.chat
- Password: (as configured in .env.production)

### 2. Green API Setup
1. Login to the admin interface
2. Click "Setup" next to Green API status
3. Enter your Green API credentials
4. Test and save credentials

### 3. Google Calendar Setup
1. Configure Google Calendar API credentials
2. Set up calendar synchronization
3. Test the integration

## Maintenance

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Backup Data
```bash
# Backup database and credentials
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Restore backup
tar -xzf backup-YYYYMMDD.tar.gz
```

### SSL Certificate Renewal
SSL certificates are automatically renewed via cron job. To manually renew:
```bash
sudo certbot renew --dry-run
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

### 2. Regular Updates
- Keep Docker images updated
- Monitor security advisories
- Update system packages regularly

### 3. Access Control
- Only admin@cig.chat can access the system
- All communication is encrypted (HTTPS)
- Credentials are encrypted at rest

## Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h
```

#### 2. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Test SSL
openssl s_client -connect evolution.cig.chat:443
```

#### 3. Database Issues
```bash
# Check database file permissions
ls -la data/database/

# Repair database (if needed)
sqlite3 data/database/wamems.db ".schema"
```

### Support
For issues and support:
1. Check logs first
2. Verify DNS configuration
3. Ensure all services are running
4. Check firewall settings

## URLs and Endpoints

- **Main Application**: https://evolution.cig.chat
- **API Base**: https://evolution.cig.chat/api
- **Admin Login**: https://evolution.cig.chat/admin/login
- **Health Check**: https://evolution.cig.chat/health
- **Green API Help**: https://evolution.cig.chat/api/green-api/help

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `ADMIN_EMAIL` | Admin email address | Yes |
| `ADMIN_PASSWORD_HASH` | Admin password hash | Yes |
| `DOMAIN` | Domain name | Yes |
| `FLASK_ENV` | Flask environment | Yes |
| `DATABASE_URL` | Database connection string | Yes |

## File Structure
```
wamems/
├── backend/                 # Python Flask backend
├── src/                    # React frontend
├── nginx/                  # Nginx configuration
├── ssl/                    # SSL certificates
├── data/                   # Application data
│   ├── database/          # SQLite database
│   ├── credentials/       # Encrypted credentials
│   └── logs/             # Application logs
├── scripts/               # Deployment scripts
├── docker-compose.yml     # Docker services
└── .env.production       # Environment configuration
```



















