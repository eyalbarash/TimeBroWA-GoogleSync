# WAMems Deployment Plan - Contabo VPS

## Overview
Deploy TimeBro WhatsApp-Google Sync system to Contabo VPS under evolution.cig.chat with Docker containerization and admin-only access.

## Target Environment
- **Server**: Contabo VPS
- **Domain**: evolution.cig.chat
- **Environment Name**: WAMems
- **Access**: admin@cig.chat only
- **Container**: Docker-based deployment

## Architecture

### 1. Docker Container Structure
```
WAMems/
├── frontend/          # React + Vite frontend
├── backend/           # Python + Flask backend
├── nginx/             # Reverse proxy + SSL
├── database/          # SQLite database
├── credentials/       # Encrypted credentials storage
└── logs/             # Application logs
```

### 2. Services
- **Frontend**: React app on port 3000 (internal)
- **Backend**: Flask API on port 8080 (internal)
- **Nginx**: Reverse proxy on ports 80/443 (external)
- **Database**: SQLite with encrypted storage
- **Credentials**: Encrypted Green API credentials

### 3. Security
- Admin authentication (admin@cig.chat)
- JWT token-based sessions
- HTTPS with Let's Encrypt SSL
- CORS configuration
- Rate limiting
- Input validation

## Implementation Steps

### Phase 1: Docker Configuration
1. Create Dockerfile for frontend
2. Create Dockerfile for backend
3. Create docker-compose.yml
4. Configure nginx reverse proxy
5. Set up SSL certificates

### Phase 2: Authentication System
1. Implement admin login system
2. JWT token management
3. Session handling
4. Password hashing
5. Login/logout endpoints

### Phase 3: Environment Setup
1. Production environment variables
2. Database configuration
3. Credential management
4. Logging configuration
5. Error handling

### Phase 4: DNS & Networking
1. Configure nginx for evolution.cig.chat
2. SSL certificate setup
3. Domain configuration
4. Firewall rules
5. Port mapping

### Phase 5: Deployment
1. Create deployment scripts
2. Backup strategies
3. Monitoring setup
4. Health checks
5. Update procedures

## Files to Create

### Docker Configuration
- `Dockerfile.frontend`
- `Dockerfile.backend`
- `docker-compose.yml`
- `nginx/nginx.conf`
- `nginx/ssl.conf`

### Authentication
- `backend/auth_manager.py`
- `backend/middleware.py`
- `frontend/auth/LoginComponent.tsx`
- `frontend/auth/AuthContext.tsx`

### Environment
- `.env.production`
- `docker-compose.prod.yml`
- `scripts/deploy.sh`
- `scripts/backup.sh`

### DNS & SSL
- `nginx/evolution.cig.chat.conf`
- `ssl/letsencrypt/`
- `scripts/ssl-setup.sh`

## Security Considerations

### Authentication
- Strong password requirements
- JWT token expiration
- Secure session management
- CSRF protection

### Network Security
- HTTPS only
- Secure headers
- Rate limiting
- IP whitelisting (optional)

### Data Protection
- Encrypted credential storage
- Secure database access
- Regular backups
- Log sanitization

## Monitoring & Maintenance

### Logging
- Application logs
- Access logs
- Error tracking
- Performance metrics

### Backup
- Database backups
- Credential backups
- Configuration backups
- Automated backup scripts

### Updates
- Container updates
- Security patches
- Feature updates
- Rollback procedures

## DNS Configuration

### A Records
- `evolution.cig.chat` → VPS IP
- `wamems.evolution.cig.chat` → VPS IP (optional)

### CNAME Records
- `api.evolution.cig.chat` → evolution.cig.chat
- `admin.evolution.cig.chat` → evolution.cig.chat

## Expected URLs
- **Main App**: https://evolution.cig.chat
- **API**: https://evolution.cig.chat/api
- **Admin**: https://evolution.cig.chat/admin
- **Health Check**: https://evolution.cig.chat/health

## Next Steps
1. Create Docker configuration files
2. Implement authentication system
3. Set up production environment
4. Configure nginx and SSL
5. Create deployment scripts
6. Test on staging environment
7. Deploy to production
8. Configure DNS
9. Monitor and maintain



















