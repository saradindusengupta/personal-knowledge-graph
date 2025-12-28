# Environment-Specific Docker Deployment Guide

## Quick Reference

### Using Different Environments

You have **3 ways** to run Neo4j with different configurations:

---

## Method 1: Using ENV_FILE Variable (Recommended)

```bash
# Development
make docker-up ENV_FILE=.env.dev

# Staging
make docker-up ENV_FILE=.env.staging

# Production
make docker-up ENV_FILE=.env.prod
```

Or with docker-compose directly:
```bash
docker-compose --env-file .env.dev up -d
docker-compose --env-file .env.staging up -d
docker-compose --env-file .env.prod up -d
```

---

## Method 2: Using Dedicated Make Commands (Easiest)

```bash
# Development (Neo4j Community, DEBUG logging, lighter resources)
make docker-dev

# Staging (full config, testing production setup)
make docker-staging

# Production (Neo4j Enterprise, optimized settings)
make docker-prod
```

---

## Method 3: Using Compose Overrides (Most Flexible)

```bash
# Development with overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d

# Production with overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d
```

---

## Environment Files Overview

| File | Purpose | Neo4j Edition | Memory | Logging |
|------|---------|---------------|--------|---------|
| `.env.dev` | Local development | Community | 1GB heap | DEBUG |
| `.env.staging` | Pre-production testing | Enterprise | 2GB heap | INFO |
| `.env.prod` | Production deployment | Enterprise | 4GB heap | INFO |

---

## Complete Workflow Examples

### Development Workflow

```bash
# 1. Start development environment
make docker-dev

# 2. Check status
make docker-status

# 3. View logs
make docker-logs

# 4. Access Neo4j
open http://localhost:7474
# Login: neo4j / dev_password_123

# 5. Stop when done
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

### Staging Workflow

```bash
# 1. Ensure .env.staging has correct passwords
cat .env.staging

# 2. Start staging
make docker-staging

# 3. Run tests against staging
# ... your tests here ...

# 4. Stop
make docker-down ENV_FILE=.env.staging
```

### Production Workflow

```bash
# 1. IMPORTANT: Update passwords in .env.prod
vim .env.prod

# 2. Build with production settings
make docker-build ENV_FILE=.env.prod

# 3. Start production
make docker-prod

# 4. Verify health
make docker-status

# 5. Setup automated backups
crontab -e
# Add: 0 2 * * * cd /path/to/project && make docker-backup
```

---

## Switching Between Environments

### From Dev to Staging
```bash
# Stop dev
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Start staging
make docker-staging
```

### From Staging to Production
```bash
# Stop staging
make docker-down ENV_FILE=.env.staging

# Backup data if migrating
make docker-backup

# Start production
make docker-prod
```

---

## Environment-Specific Features

### Development (.env.dev)
- ✅ Neo4j Community Edition (free)
- ✅ DEBUG logging enabled
- ✅ Query parameter logging
- ✅ Local code mounted for live changes
- ✅ Lower resource requirements
- ✅ Relaxed security for easier testing

### Staging (.env.staging)
- ✅ Neo4j Enterprise Edition
- ✅ INFO logging
- ✅ Production-like resource allocation
- ✅ Full backup capabilities
- ✅ Monitoring enabled

### Production (.env.prod)
- ✅ Neo4j Enterprise Edition
- ✅ Maximum security settings
- ✅ Full resource allocation
- ✅ SSL/TLS ready
- ✅ Automated backups
- ✅ Advanced monitoring
- ✅ No source code mounts

---

## Configuration Customization

### Override Specific Settings

Create a custom `.env.custom`:
```bash
cp .env.dev .env.custom
# Edit .env.custom with your settings
make docker-up ENV_FILE=.env.custom
```

### Temporary Override
```bash
# Override password for one-time use
NEO4J_PASSWORD=temp_pass docker-compose --env-file .env.dev up -d

# Or combine multiple overrides
NEO4J_PASSWORD=mypass NEO4J_HEAP_MAX=3G docker-compose up -d
```

---

## Makefile Commands Summary

```bash
# Environment-specific
make docker-dev          # Start development environment
make docker-staging      # Start staging environment
make docker-prod         # Start production environment

# With ENV_FILE variable
make docker-up ENV_FILE=.env.dev
make docker-down ENV_FILE=.env.dev
make docker-build ENV_FILE=.env.prod

# Standard commands
make docker-status       # Check current status
make docker-logs         # View logs
make docker-backup       # Create backup
make docker-clean        # Remove all (with confirmation)
```

---

## Best Practices

### 1. **Never Commit .env Files**
```bash
# Already in .gitignore, but be careful!
git status  # Always check before committing
```

### 2. **Use Secrets Management in Production**
```bash
# Option 1: Docker secrets (Swarm)
echo "my_secret_password" | docker secret create neo4j_password -

# Option 2: Environment variables from CI/CD
# Set in GitHub Actions, GitLab CI, etc.

# Option 3: External secrets manager
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### 3. **Different Data Volumes per Environment**
If running multiple environments on same host:
```bash
# In docker-compose.dev.yml
volumes:
  neo4j_data_dev:
    driver: local

# In docker-compose.prod.yml
volumes:
  neo4j_data_prod:
    driver: local
```

### 4. **Isolate Networks**
```bash
# Development network
networks:
  dev-network:
    driver: bridge

# Production network
networks:
  prod-network:
    driver: bridge
```

---

## Troubleshooting

### Wrong environment running?
```bash
# Check which containers are running
docker ps

# Check environment variables
docker-compose --env-file .env.dev config

# See actual values being used
make docker-status
```

### Env file not found?
```bash
# Ensure file exists
ls -la .env*

# Create from example
cp .env.example .env.dev
```

### Permission denied?
```bash
# Fix .env file permissions
chmod 600 .env*
```

---

## Security Checklist by Environment

### Development ✓
- [x] Simple password OK
- [x] Exposed ports OK
- [x] Debug logging OK

### Staging ✓
- [x] Strong password
- [x] Limited port exposure
- [x] INFO logging
- [x] Test backup procedures

### Production ✓
- [x] Very strong password (20+ chars)
- [x] Firewall configured
- [x] SSL/TLS enabled
- [x] Automated backups configured
- [x] Monitoring active
- [x] Secrets in vault (not .env file)
- [x] Regular security updates

---

## Quick Command Reference Card

```bash
# Development
make docker-dev              # Start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down  # Stop

# Staging
make docker-staging          # Start
make docker-down ENV_FILE=.env.staging  # Stop

# Production
make docker-prod             # Start
make docker-down ENV_FILE=.env.prod  # Stop

# Logs
make docker-logs             # Follow logs
docker-compose logs --tail=100 neo4j  # Last 100 lines

# Backup
make docker-backup           # Create backup now

# Clean
make docker-clean            # Remove everything (asks confirmation)
```

---

For more details, see [DEPLOYMENT.md](DEPLOYMENT.md)
