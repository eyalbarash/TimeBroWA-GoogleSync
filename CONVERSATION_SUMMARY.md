# Conversation Summary - Evolution API Troubleshooting
**Date**: October 5, 2025
**Project**: TimeBroWA-GoogleSync (WAMems)
**Server**: evolution.cig.chat (45.159.220.65)

## Critical Issue Identified

### Problem
The user reported that `https://evolution-api.cig.chat/manager/` was not accessible after attempting to deploy WAMems to the server. This was a production site that was working before.

### Root Cause Analysis

1. **SSL Certificate Missing**
   - evolution-api.cig.chat had no SSL certificate configured
   - Nginx was not listening on port 443 (HTTPS)
   - Only HTTP (port 80) was working

2. **Port Configuration Changes**
   - Evolution API was changed from port 8080 to port 3000
   - Nginx configuration was still pointing to port 8080
   - This mismatch caused the service to be inaccessible

3. **Redis Configuration Missing**
   - `REDIS_URI` and `REDIS_PREFIX` were missing from `.env`
   - Evolution API was showing continuous "redis disconnected" errors
   - Redis container was running but not properly connected

4. **Coolify Services Stopped**
   - Coolify and coolify-proxy containers were in "Exited" state
   - Coolify was looking for `coolify-redis` which didn't exist
   - This affected the overall server management

5. **No Proper Backup**
   - Only a partial backup was created (`/root/backup-20251005-0316/`)
   - Backup contained only container list, not full configuration
   - `.env` file was not backed up initially (though an automatic backup existed)

## Actions Taken

### 1. SSL Certificate Creation
```bash
certbot certonly --standalone -d evolution-api.cig.chat \
  --non-interactive --agree-tos --email admin@cig.chat
```

### 2. Nginx Configuration Update
Created proper nginx config at `/etc/nginx/sites-available/evolution-api`:
```nginx
server {
    listen 80;
    server_name evolution-api.cig.chat;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name evolution-api.cig.chat;

    ssl_certificate /etc/letsencrypt/live/evolution-api.cig.chat/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/evolution-api.cig.chat/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3. Redis Configuration Added
Updated `/home/evolution/evolution-api/.env`:
```env
DATABASE_CONNECTION_URI=postgresql://user:pass@postgres:5432/evolution?schema=public
API_KEY=abc123xyz789qwerty456
GLOBAL_TOKEN=abc123xyz789qwerty456
PORT=3000
DATABASE_PROVIDER=postgresql
REDIS_URI=redis://redis:6379
REDIS_PREFIX=evolution
```

### 4. Evolution API Restart
```bash
cd /home/evolution/evolution-api
docker compose restart api
```

## Current Status

### ✅ Working
- evolution-api.cig.chat is accessible via HTTPS (200 OK)
- SSL certificate installed and valid (expires 2026-01-02)
- Docker containers running:
  - evolution_api (Up)
  - postgres (Up)
  - redis (Up)

### ⚠️ Issues Remaining
- Redis warnings still appearing in logs (but service works)
- Coolify and coolify-proxy are stopped
- Port mismatch: evolution_api runs on port 3000, nginx points to 8080
- No comprehensive backup system in place

## Configuration Details

### Original Database Credentials
```
Username: user
Password: pass
Host: postgres
Port: 5432
Database: evolution
Schema: public
```

### Port Mappings
- **coolify-proxy (Traefik)**: 80, 443, 8080
- **coolify**: 8000 → 8080 (internal)
- **evolution_api**: 3000 (internal)
- **postgres**: 5433 → 5432 (changed to avoid conflict)
- **redis**: 6379

### Docker Volumes Found
```
c844osogw8ggkko8gwk8wo44_evolution-instances (old Coolify deployment)
c844osogw8ggkko8gwk8wo44_evolution-redis (old Coolify deployment)
c844osogw8ggkko8gwk8wo44_postgres-data (old Coolify deployment)
evolution-api_evolution_instances (current)
evolution-api_evolution_redis (current)
evolution-api_postgres_data (current)
```

## Lessons Learned

1. **Always create full backups before making changes**
   - Include all configuration files (.env, docker-compose.yaml, nginx configs)
   - Document current state (running containers, ports, volumes)
   - Test backup restoration process

2. **Port conflicts are critical**
   - Document all port usage before changes
   - Check for conflicts with existing services (Coolify, Traefik)
   - Maintain consistency between docker-compose and nginx configs

3. **SSL certificates are essential for production**
   - Always verify HTTPS is working
   - Set up automatic renewal
   - Test certificate installation

4. **Redis configuration is required**
   - Evolution API requires Redis connection
   - Must specify REDIS_URI and REDIS_PREFIX
   - Verify connection after configuration

## Recommendations

### Immediate Actions Needed
1. Fix nginx to point to correct port (3000 instead of 8080) OR change evolution_api back to port 8080
2. Restart Coolify services if needed for server management
3. Create comprehensive backup of current working state
4. Document all changes made

### Long-term Improvements
1. Implement automated backup system
2. Set up monitoring for all services
3. Create runbook for common issues
4. Use infrastructure as code (IaC) for reproducibility
5. Implement proper change management process

## Files Modified

1. `/home/evolution/evolution-api/.env` - Added Redis configuration
2. `/home/evolution/evolution-api/docker-compose.yaml` - Port changed to 3000
3. `/etc/nginx/sites-available/evolution-api` - Created/updated nginx config
4. `/etc/letsencrypt/live/evolution-api.cig.chat/` - SSL certificates created

## Backup Files Found

- `/root/backup-20251005-0316/` - Partial backup (container list only)
- `/home/evolution/evolution-api/.env.backup.20251005_043816` - Automatic .env backup

## Next Steps

User requested to:
1. Not make any system changes yet
2. Verify what services were created on port 8080
3. Check original database credentials
4. Export conversation to text files

---

**Status**: evolution-api.cig.chat is now accessible, but configuration inconsistencies remain that need to be addressed.
















