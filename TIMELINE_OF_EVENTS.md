# Timeline of Events - Evolution API Incident

## October 5, 2025

### Early Morning (02:00 - 03:00 CEST)

**02:16 AM** - Manual backup created
- Location: `/root/backup-20251005-0316/`
- Content: Container list snapshot
- Note: Incomplete backup, missing configuration files

**02:19 AM** - Coolify container stopped
- Container: coolify (ghcr.io/coollabsio/coolify:4.0.0-beta.432)
- Status: Exited (137) - Killed by signal
- Impact: Server management interface unavailable

**01:59 AM** - Coolify-proxy (Traefik) created
- Container: coolify-proxy (traefik:v3.1)
- Later stopped around 02:00 AM

### Morning (03:00 - 05:00 CEST)

**03:38 AM** - New Docker containers created
- postgres container created
- redis container created
- Reason: Fresh deployment attempt

**03:39 AM** - Evolution API container created
- Container: evolution_api (atendai/evolution-api:latest)
- Port configuration: 3000:3000
- Issue: Changed from original 8080 to 3000

**04:38 AM** - Automatic .env backup created
- File: `.env.backup.20251005_043816`
- Content: Complete environment variables
- Trigger: Automatic backup before changes

### Issue Discovery (Late Morning)

**User Report**: evolution-api.cig.chat/manager/ not accessible
- Site was working before
- Production environment
- Critical service outage

### Investigation Phase

**Initial Findings**:
1. HTTPS not working (SSL certificate missing)
2. Nginx not listening on port 443
3. HTTP (port 80) returning connection errors
4. Redis disconnection errors in logs

**Root Causes Identified**:
1. No SSL certificate for evolution-api.cig.chat
2. Port mismatch: nginx → 8080, evolution_api → 3000
3. Missing Redis configuration in .env
4. Coolify services stopped

### Resolution Phase

**Step 1: SSL Certificate Creation**
- Time: During troubleshooting session
- Action: Created Let's Encrypt certificate using certbot standalone
- Result: Certificate valid until January 2, 2026
- Command: `certbot certonly --standalone -d evolution-api.cig.chat`

**Step 2: Nginx Configuration**
- Created proper nginx config with SSL
- Added HTTP to HTTPS redirect
- Configured reverse proxy to localhost:8080
- Note: Port still incorrect (should be 3000)

**Step 3: Redis Configuration**
- Added to .env:
  - REDIS_URI=redis://redis:6379
  - REDIS_PREFIX=evolution
- Restarted evolution_api container
- Result: Redis errors reduced but not eliminated

**Step 4: Service Restart**
- Command: `docker compose restart api`
- Evolution API restarted successfully
- Database migrations ran successfully
- Prisma client generated

### Current Status (As of conversation end)

**Working**:
- ✅ evolution-api.cig.chat accessible via HTTPS
- ✅ SSL certificate installed and valid
- ✅ Docker containers running (api, redis, postgres)
- ✅ HTTP 200 response from /manager/

**Issues Remaining**:
- ⚠️ Port mismatch (nginx → 8080, app → 3000)
- ⚠️ Redis warnings in logs
- ⚠️ Coolify services stopped
- ⚠️ No comprehensive backup system

## Key Decisions Made

### Decision 1: Port Change (3000 instead of 8080)
- **When**: During initial deployment
- **Reason**: Conflict with coolify-proxy on port 8080
- **Impact**: Created mismatch with nginx configuration
- **Status**: Needs correction

### Decision 2: PostgreSQL Port Mapping (5433:5432)
- **When**: During postgres container setup
- **Reason**: Avoid conflict with system PostgreSQL
- **Impact**: Successful, no issues
- **Status**: Working correctly

### Decision 3: Add Redis Configuration
- **When**: During troubleshooting
- **Reason**: Evolution API requires Redis connection
- **Impact**: Reduced errors, improved stability
- **Status**: Partially working

### Decision 4: Create SSL Certificate
- **When**: During troubleshooting
- **Reason**: HTTPS required for production
- **Impact**: Enabled secure access
- **Status**: Working correctly

## Changes Made to System

### Files Modified

1. **`/home/evolution/evolution-api/.env`**
   - Added: REDIS_URI
   - Added: REDIS_PREFIX
   - Kept: All other variables unchanged

2. **`/home/evolution/evolution-api/docker-compose.yaml`**
   - Changed: Port mapping from 8080:8080 to 3000:3000
   - Changed: postgres port from 5432:5432 to 5433:5432
   - Status: Working but inconsistent with nginx

3. **`/etc/nginx/sites-available/evolution-api`**
   - Created: New configuration file
   - Added: SSL certificate configuration
   - Added: HTTP to HTTPS redirect
   - Issue: Points to wrong port (8080 instead of 3000)

4. **`/etc/letsencrypt/live/evolution-api.cig.chat/`**
   - Created: SSL certificates
   - Status: Valid and working

### Services Affected

1. **evolution_api**
   - Action: Restarted
   - Status: Running
   - Impact: Brief downtime during restart

2. **nginx**
   - Action: Configuration updated and reloaded
   - Status: Running
   - Impact: Brief configuration reload

3. **coolify**
   - Action: Stopped (not by us)
   - Status: Exited
   - Impact: Management interface unavailable

4. **coolify-proxy**
   - Action: Stopped (not by us)
   - Status: Exited
   - Impact: Traefik proxy unavailable

## Lessons from Timeline

### What Went Wrong

1. **Insufficient Backup**
   - Only container list was backed up
   - Configuration files not included
   - No verification of backup completeness

2. **Port Conflict Not Anticipated**
   - Changed port without updating all references
   - Created inconsistency between services
   - No documentation of port usage

3. **Incomplete Configuration**
   - Redis configuration missing initially
   - Database provider not specified
   - Led to service errors

4. **Coolify Dependency Not Understood**
   - Coolify services stopped unexpectedly
   - Impact on system not fully assessed
   - No plan for Coolify-less operation

### What Went Right

1. **Automatic Backup Existed**
   - .env.backup.20251005_043816 saved the day
   - Allowed verification of original configuration
   - Prevented data loss

2. **Quick SSL Setup**
   - Let's Encrypt certificate created quickly
   - Certbot worked smoothly
   - HTTPS restored rapidly

3. **Docker Compose Resilience**
   - Containers restarted successfully
   - Data persisted in volumes
   - No data corruption

4. **Systematic Troubleshooting**
   - Issues identified methodically
   - Logs examined thoroughly
   - Root causes found

## Prevention Measures for Future

### Before Making Changes

1. **Create comprehensive backup**
   - All configuration files
   - Docker compose files
   - Environment variables
   - Nginx configurations
   - SSL certificates

2. **Document current state**
   - Running containers
   - Port mappings
   - Network configuration
   - Volume usage

3. **Test in staging first**
   - Never test in production
   - Verify all changes work
   - Check for conflicts

### During Changes

1. **Change one thing at a time**
   - Easier to identify issues
   - Simpler to rollback
   - Better understanding of impact

2. **Verify after each change**
   - Test service accessibility
   - Check logs for errors
   - Confirm expected behavior

3. **Keep notes**
   - Document what was changed
   - Record why it was changed
   - Note any issues encountered

### After Changes

1. **Verify all services**
   - Check all endpoints
   - Test full functionality
   - Monitor for errors

2. **Update documentation**
   - Record new configuration
   - Update runbooks
   - Share knowledge

3. **Create new backup**
   - Backup working state
   - Verify backup is complete
   - Test restoration process

## Open Questions

1. Why did Coolify stop?
2. Was there a deployment attempt that failed?
3. What triggered the port change from 8080 to 3000?
4. Are there other services affected we haven't discovered?
5. What was the original deployment method (Coolify vs manual)?

## Next Steps Required

1. **Fix port mismatch**
   - Either change nginx to point to 3000
   - Or change evolution_api back to 8080
   - Ensure consistency

2. **Investigate Coolify**
   - Determine why it stopped
   - Decide if it should be restarted
   - Plan for Coolify vs manual management

3. **Implement proper backup**
   - Create backup script
   - Schedule regular backups
   - Test restoration procedure

4. **Document everything**
   - Create runbooks
   - Document architecture
   - Share knowledge with team

5. **Set up monitoring**
   - Health checks for all services
   - Alert on failures
   - Log aggregation

---

**Timeline Compiled**: October 5, 2025
**Incident Status**: Partially Resolved
**Follow-up Required**: Yes
















