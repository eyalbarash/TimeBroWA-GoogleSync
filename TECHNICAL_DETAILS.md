# Technical Details - Evolution API Configuration

## Server Information
- **Server**: evolution.cig.chat
- **IP Address**: 45.159.220.65
- **OS**: Ubuntu (Linux)
- **Container Runtime**: Docker with Docker Compose

## Docker Containers Status

### Currently Running
```
CONTAINER ID   IMAGE                           PORTS                                         NAMES
c32152a28cbf   atendai/evolution-api:latest    0.0.0.0:3000->3000/tcp                       evolution_api
37e320704f4b   redis:latest                    0.0.0.0:6379->6379/tcp                       redis
cb857f5b90ce   postgres:15                     0.0.0.0:5433->5432/tcp                       postgres
```

### Stopped Containers
```
4f109a542d37   ghcr.io/coollabsio/coolify:4.0.0-beta.432   Exited (137)   coolify
e9ee88878722   traefik:v3.1                                Exited (0)     coolify-proxy
```

## Evolution API Configuration

### Docker Compose File
Location: `/home/evolution/evolution-api/docker-compose.yaml`

```yaml
services:
  api:
    container_name: evolution_api
    image: atendai/evolution-api:homolog
    restart: always
    depends_on:
      - redis
      - postgres
    ports:
      - 3000:3000
    volumes:
      - evolution_instances:/evolution/instances
    networks:
      - evolution-net
    env_file:
      - .env
    expose:
      - 8080

  redis:
    image: redis:latest
    networks:
      - evolution-net
    container_name: redis
    command: >
      redis-server --port 6379 --appendonly yes
    volumes:
      - evolution_redis:/data
    ports:
      - 6379:6379

  postgres:
    container_name: postgres
    image: postgres:15
    networks:
      - evolution-net
    command: ["postgres", "-c", "max_connections=1000", "-c", "listen_addresses=*"]
    restart: always
    ports:
      - 5433:5432
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=evolution
      - POSTGRES_HOST_AUTH_METHOD=trust
    volumes:
      - postgres_data:/var/lib/postgresql/data
    expose:
      - 5432

volumes:
  evolution_instances:
  evolution_redis:
  postgres_data:

networks:
  evolution-net:
    name: evolution-net
    driver: bridge
```

### Environment Variables (.env)
Location: `/home/evolution/evolution-api/.env`

```env
DATABASE_CONNECTION_URI=postgresql://user:pass@postgres:5432/evolution?schema=public
API_KEY=abc123xyz789qwerty456
GLOBAL_TOKEN=abc123xyz789qwerty456
PORT=3000
DATABASE_PROVIDER=postgresql
REDIS_URI=redis://redis:6379
REDIS_PREFIX=evolution
```

## Nginx Configuration

### Configuration File
Location: `/etc/nginx/sites-available/evolution-api`

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
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Note**: There's a mismatch - nginx proxies to port 8080, but evolution_api runs on port 3000!

## SSL Certificate

### Certificate Details
- **Domain**: evolution-api.cig.chat
- **Issuer**: Let's Encrypt
- **Certificate Path**: `/etc/letsencrypt/live/evolution-api.cig.chat/fullchain.pem`
- **Key Path**: `/etc/letsencrypt/live/evolution-api.cig.chat/privkey.pem`
- **Expiration**: January 2, 2026
- **Auto-renewal**: Configured via certbot

### Certificate Creation Command
```bash
certbot certonly --standalone -d evolution-api.cig.chat \
  --non-interactive --agree-tos --email admin@cig.chat
```

## Port Usage Analysis

### Port 80 (HTTP)
- **Used by**: nginx
- **Purpose**: HTTP traffic, redirects to HTTPS

### Port 443 (HTTPS)
- **Used by**: nginx
- **Purpose**: HTTPS traffic, proxies to backend

### Port 3000
- **Used by**: evolution_api container
- **Purpose**: Evolution API application
- **Exposed to**: Host (0.0.0.0:3000)

### Port 5432
- **Used by**: postgres container (internal)
- **Mapped to**: Host port 5433
- **Reason**: Avoid conflict with system PostgreSQL

### Port 6379
- **Used by**: redis container
- **Purpose**: Redis cache/data store
- **Exposed to**: Host (0.0.0.0:6379)

### Port 8000
- **Used by**: coolify container (when running)
- **Purpose**: Coolify dashboard
- **Maps to**: Internal port 8080

### Port 8080
- **Used by**: coolify-proxy (Traefik) when running
- **Purpose**: Traefik proxy
- **Conflict**: nginx is trying to proxy to this port for evolution_api

## Database Configuration

### PostgreSQL
- **Version**: 15
- **Container**: postgres
- **Host**: postgres (Docker network)
- **Port**: 5432 (internal), 5433 (external)
- **Database**: evolution
- **User**: user
- **Password**: pass
- **Max Connections**: 1000
- **Auth Method**: trust

### Connection String
```
postgresql://user:pass@postgres:5432/evolution?schema=public
```

## Redis Configuration

### Redis Server
- **Version**: latest
- **Container**: redis
- **Host**: redis (Docker network)
- **Port**: 6379
- **Persistence**: AOF (Append Only File) enabled
- **Data Volume**: evolution_redis

### Connection String
```
redis://redis:6379
```

## Docker Volumes

### Active Volumes
```
evolution-api_evolution_instances  - Evolution API instance data
evolution-api_evolution_redis      - Redis data
evolution-api_postgres_data        - PostgreSQL data
```

### Legacy Volumes (from Coolify)
```
c844osogw8ggkko8gwk8wo44_evolution-instances
c844osogw8ggkko8gwk8wo44_evolution-redis
c844osogw8ggkko8gwk8wo44_postgres-data
```

## Network Configuration

### Docker Network
- **Name**: evolution-net
- **Driver**: bridge
- **Connected Services**: api, redis, postgres

## Coolify Configuration

### Coolify Status
- **Container**: coolify (Exited)
- **Proxy**: coolify-proxy (Traefik, Exited)
- **Dashboard Port**: 8000
- **Issue**: Looking for coolify-redis which doesn't exist

### Coolify vs Manual Deployment
- **Old deployment**: Managed by Coolify (c844osogw8ggkko8gwk8wo44 prefix)
- **Current deployment**: Manual docker-compose (evolution-api prefix)
- **Conflict**: Both trying to use similar resources

## Logs and Diagnostics

### Evolution API Logs
```bash
docker logs evolution_api
```

**Common Issues**:
- Redis disconnected errors (before REDIS_URI was added)
- Database connection issues (before DATABASE_PROVIDER was set)

### Redis Logs
```bash
docker logs redis
```

**Status**: Running normally with modules loaded (search, timeseries, ReJSON)

### PostgreSQL Logs
```bash
docker logs postgres
```

**Status**: Running normally, accepting connections

## Backup Information

### Automatic Backup
- **Location**: `/home/evolution/evolution-api/.env.backup.20251005_043816`
- **Content**: Complete .env file
- **Created**: October 5, 2025, 04:38:16

### Manual Backup
- **Location**: `/root/backup-20251005-0316/`
- **Content**: Container list only
- **Created**: October 5, 2025, 03:16

### Backup Command Used
```bash
docker ps -a > /root/backup-20251005-0316/current_containers.txt
```

## API Keys and Tokens

### Evolution API
- **API_KEY**: abc123xyz789qwerty456
- **GLOBAL_TOKEN**: abc123xyz789qwerty456

### Historical API Keys (from bash history)
- 38E5AB80EE3F-419A-BE86-B5473EEC8DD1
- 0196BB44-1C74-42C4-9712-13CD45F5FFCE
- tfp9usq1YAqOwElzCvi6kkY8x6Mof2Zs

## Known Issues

1. **Port Mismatch**: nginx proxies to 8080, but evolution_api runs on 3000
2. **Redis Warnings**: Continuous "redis disconnected" warnings in logs
3. **Coolify Stopped**: Management interface not available
4. **No Comprehensive Backup**: Only partial backups exist
5. **Legacy Volumes**: Old Coolify volumes still present

## Testing Commands

### Check Service Status
```bash
# Check if evolution-api is accessible
curl -I https://evolution-api.cig.chat/manager/

# Check Docker containers
docker ps -a

# Check logs
docker logs evolution_api
docker logs redis
docker logs postgres

# Check ports
netstat -tlnp | grep -E '(80|443|3000|5432|6379|8080)'
```

### Database Connection Test
```bash
docker exec -it postgres psql -U user -d evolution
```

### Redis Connection Test
```bash
docker exec redis redis-cli ping
```

## Recovery Procedures

### Restore .env from Backup
```bash
cp /home/evolution/evolution-api/.env.backup.20251005_043816 \
   /home/evolution/evolution-api/.env
```

### Restart All Services
```bash
cd /home/evolution/evolution-api
docker compose down
docker compose up -d
```

### Fix Nginx Port Configuration
```bash
# Edit nginx config to point to port 3000
sed -i 's/localhost:8080/localhost:3000/g' /etc/nginx/sites-available/evolution-api
nginx -t
systemctl reload nginx
```

## Monitoring Recommendations

1. Set up health checks for all services
2. Monitor SSL certificate expiration
3. Track Redis connection status
4. Monitor database connections
5. Set up alerts for container failures
6. Implement log aggregation

---

**Last Updated**: October 5, 2025
**Maintained By**: System Administrator
















