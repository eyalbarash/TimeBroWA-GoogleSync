# Action Items - Evolution API Recovery

## 🔴 Critical (Must Do Immediately)

### 1. Fix Port Mismatch
**Priority**: CRITICAL  
**Impact**: Service may not work correctly  
**Status**: ⏳ Pending

**Problem**:
- Nginx proxies to `localhost:8080`
- Evolution API runs on port `3000`
- This mismatch may cause issues

**Options**:

**Option A: Update Nginx (Recommended)**
```bash
# Edit nginx config
sudo nano /etc/nginx/sites-available/evolution-api

# Change line:
# FROM: proxy_pass http://localhost:8080;
# TO:   proxy_pass http://localhost:3000;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

**Option B: Change Evolution API Port**
```bash
# Edit docker-compose.yaml
cd /home/evolution/evolution-api
nano docker-compose.yaml

# Change:
# FROM: - 3000:3000
# TO:   - 8080:8080

# Edit .env
nano .env
# Change:
# FROM: PORT=3000
# TO:   PORT=8080

# Restart
docker compose down
docker compose up -d
```

**Recommendation**: Choose Option A (update nginx) as it's less disruptive.

---

### 2. Create Comprehensive Backup
**Priority**: CRITICAL  
**Impact**: Data loss prevention  
**Status**: ⏳ Pending

**What to Backup**:
1. All configuration files
2. Docker compose files
3. Environment variables
4. Nginx configurations
5. SSL certificates
6. Database dumps

**Backup Script**:
```bash
#!/bin/bash
BACKUP_DIR="/root/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Configuration files
cp /home/evolution/evolution-api/.env "$BACKUP_DIR/"
cp /home/evolution/evolution-api/docker-compose.yaml "$BACKUP_DIR/"

# Nginx configs
cp -r /etc/nginx/sites-available/evolution-api "$BACKUP_DIR/"

# SSL certificates
cp -r /etc/letsencrypt/live/evolution-api.cig.chat "$BACKUP_DIR/" 2>/dev/null || true

# Docker state
docker ps -a > "$BACKUP_DIR/docker_containers.txt"
docker volume ls > "$BACKUP_DIR/docker_volumes.txt"
docker network ls > "$BACKUP_DIR/docker_networks.txt"

# Database dump
docker exec postgres pg_dump -U user evolution > "$BACKUP_DIR/evolution_db.sql"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
echo "Backup created: $BACKUP_DIR.tar.gz"
```

---

### 3. Verify All Services Working
**Priority**: HIGH  
**Impact**: Ensure production stability  
**Status**: ⏳ Pending

**Tests to Run**:

```bash
# 1. Check HTTPS access
curl -I https://evolution-api.cig.chat/manager/

# 2. Check API health
curl -H "apikey: abc123xyz789qwerty456" \
  https://evolution-api.cig.chat/instance/fetchInstances

# 3. Check database connection
docker exec postgres psql -U user -d evolution -c "SELECT version();"

# 4. Check Redis connection
docker exec redis redis-cli ping

# 5. Check all containers running
docker ps

# 6. Check logs for errors
docker logs evolution_api --tail 50
docker logs redis --tail 20
docker logs postgres --tail 20
```

---

## 🟡 Important (Should Do Soon)

### 4. Investigate Coolify Status
**Priority**: MEDIUM  
**Impact**: Server management capability  
**Status**: ⏳ Pending

**Questions to Answer**:
1. Why did Coolify stop?
2. Is it needed for current setup?
3. Should it be restarted?
4. What's the migration plan?

**Investigation Steps**:
```bash
# Check Coolify logs
docker logs coolify --tail 100

# Check coolify-proxy logs
docker logs coolify-proxy --tail 100

# Check if Coolify is managing evolution-api
docker inspect evolution_api | grep -i coolify

# List all Coolify-related containers
docker ps -a | grep coolify

# Check Coolify volumes
docker volume ls | grep c844osogw8ggkko8gwk8wo44
```

**Decision Required**: 
- Continue with Coolify?
- Migrate to manual management?
- Hybrid approach?

---

### 5. Fix Redis Warnings
**Priority**: MEDIUM  
**Impact**: Log noise, potential instability  
**Status**: ⏳ Pending

**Current Issue**:
- Continuous "redis disconnected" warnings in logs
- Even though REDIS_URI is configured

**Investigation Steps**:
```bash
# Check Redis logs
docker logs redis

# Check Evolution API Redis connection
docker exec evolution_api env | grep REDIS

# Test Redis connection from evolution_api container
docker exec evolution_api ping redis

# Check Redis network connectivity
docker network inspect evolution-net
```

**Possible Solutions**:
1. Verify Redis is in same Docker network
2. Check Redis authentication requirements
3. Review Evolution API Redis configuration
4. Check for Redis connection pooling issues

---

### 6. Clean Up Legacy Volumes
**Priority**: LOW  
**Impact**: Disk space, clarity  
**Status**: ⏳ Pending

**Legacy Volumes Found**:
```
c844osogw8ggkko8gwk8wo44_evolution-instances
c844osogw8ggkko8gwk8wo44_evolution-redis
c844osogw8ggkko8gwk8wo44_postgres-data
```

**Before Removing**:
1. Verify they're not in use
2. Check if they contain important data
3. Create backup if needed
4. Document what they contained

**Removal Commands** (only after verification):
```bash
# List volumes and their usage
docker volume ls
docker ps -a --filter volume=c844osogw8ggkko8gwk8wo44_evolution-instances

# If safe to remove:
docker volume rm c844osogw8ggkko8gwk8wo44_evolution-instances
docker volume rm c844osogw8ggkko8gwk8wo44_evolution-redis
docker volume rm c844osogw8ggkko8gwk8wo44_postgres-data
```

---

## 📋 Documentation Tasks

### 7. Create System Documentation
**Priority**: MEDIUM  
**Status**: ✅ Partially Complete

**Documents Created**:
- ✅ CONVERSATION_SUMMARY.md
- ✅ TECHNICAL_DETAILS.md
- ✅ TIMELINE_OF_EVENTS.md
- ✅ ACTION_ITEMS.md (this file)

**Still Needed**:
- [ ] Architecture diagram
- [ ] Runbook for common issues
- [ ] Deployment guide
- [ ] Rollback procedures
- [ ] Monitoring setup guide

---

### 8. Update Configuration Management
**Priority**: MEDIUM  
**Status**: ⏳ Pending

**Tasks**:
1. Document all environment variables
2. Create configuration templates
3. Set up version control for configs
4. Implement configuration validation
5. Create change management process

---

## 🔧 Operational Improvements

### 9. Implement Monitoring
**Priority**: HIGH  
**Status**: ⏳ Pending

**What to Monitor**:
1. Service uptime (evolution-api, redis, postgres)
2. SSL certificate expiration
3. Disk space usage
4. Container health
5. Log errors
6. Response times

**Suggested Tools**:
- Uptime monitoring: UptimeRobot, Pingdom
- Container monitoring: Portainer, Watchtower
- Log aggregation: Loki, ELK stack
- Metrics: Prometheus + Grafana

---

### 10. Set Up Automated Backups
**Priority**: HIGH  
**Status**: ⏳ Pending

**Backup Strategy**:
1. **Daily backups**: Configuration files, database
2. **Weekly backups**: Full system state
3. **Monthly backups**: Long-term archive
4. **Retention**: 7 daily, 4 weekly, 12 monthly

**Implementation**:
```bash
# Create backup script (see item #2)
# Add to crontab
crontab -e

# Add lines:
# Daily backup at 2 AM
0 2 * * * /root/scripts/backup.sh

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /root/scripts/full-backup.sh

# Test backup restoration monthly
0 4 1 * * /root/scripts/test-restore.sh
```

---

### 11. Implement Health Checks
**Priority**: MEDIUM  
**Status**: ⏳ Pending

**Health Check Script**:
```bash
#!/bin/bash
# health-check.sh

echo "=== Evolution API Health Check ==="
echo "Timestamp: $(date)"

# Check HTTPS
echo -n "HTTPS: "
if curl -sf https://evolution-api.cig.chat/manager/ > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check containers
echo -n "Containers: "
RUNNING=$(docker ps --filter "name=evolution_api" --filter "status=running" -q | wc -l)
if [ "$RUNNING" -eq 1 ]; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check database
echo -n "Database: "
if docker exec postgres psql -U user -d evolution -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check Redis
echo -n "Redis: "
if docker exec redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Check disk space
echo -n "Disk Space: "
USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$USAGE" -lt 80 ]; then
    echo "✅ OK ($USAGE%)"
else
    echo "⚠️ WARNING ($USAGE%)"
fi

echo "=== End Health Check ==="
```

---

## 🎯 Long-term Goals

### 12. Infrastructure as Code
**Priority**: LOW  
**Status**: ⏳ Pending

**Goals**:
1. Version control all configurations
2. Automate deployment
3. Enable easy rollback
4. Improve reproducibility

**Suggested Tools**:
- Ansible for configuration management
- Terraform for infrastructure
- Git for version control
- CI/CD pipeline for automation

---

### 13. Disaster Recovery Plan
**Priority**: MEDIUM  
**Status**: ⏳ Pending

**Plan Components**:
1. Backup verification procedures
2. Restoration procedures
3. Failover procedures
4. Communication plan
5. Testing schedule

**Recovery Time Objectives**:
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 24 hours

---

## 📊 Status Summary

| Priority | Total | Pending | In Progress | Complete |
|----------|-------|---------|-------------|----------|
| Critical | 3     | 3       | 0           | 0        |
| High     | 3     | 3       | 0           | 0        |
| Medium   | 5     | 4       | 0           | 1        |
| Low      | 2     | 2       | 0           | 0        |
| **Total**| **13**| **12**  | **0**       | **1**    |

---

## 🗓️ Suggested Timeline

### Week 1 (Immediate)
- [ ] Day 1: Fix port mismatch (#1)
- [ ] Day 1: Create comprehensive backup (#2)
- [ ] Day 2: Verify all services (#3)
- [ ] Day 3: Investigate Coolify (#4)
- [ ] Day 4-5: Fix Redis warnings (#5)

### Week 2 (Important)
- [ ] Implement monitoring (#9)
- [ ] Set up automated backups (#10)
- [ ] Implement health checks (#11)
- [ ] Create remaining documentation (#7)

### Week 3-4 (Improvements)
- [ ] Clean up legacy volumes (#6)
- [ ] Update configuration management (#8)
- [ ] Create disaster recovery plan (#13)

### Month 2+ (Long-term)
- [ ] Infrastructure as Code (#12)
- [ ] Advanced monitoring and alerting
- [ ] Performance optimization
- [ ] Security hardening

---

**Document Created**: October 5, 2025  
**Last Updated**: October 5, 2025  
**Owner**: System Administrator  
**Review Schedule**: Weekly until all critical items complete
















