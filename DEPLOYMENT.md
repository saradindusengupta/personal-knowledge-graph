# Neo4j Production Deployment Guide

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 20GB+ disk space for data
- Open ports: 7474 (HTTP), 7473 (HTTPS), 7687 (Bolt)

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your production values
nano .env  # or vim, code, etc.
```

**Important:** Change the default password in `.env`!

### 2. Build and Deploy

```bash
# Build the Docker image
docker-compose build

# Start Neo4j in production mode
docker-compose up -d

# Check logs
docker-compose logs -f neo4j

# Verify health
docker-compose ps
```

### 3. Access Neo4j

- **Browser Interface:** http://localhost:7474
- **Bolt Protocol:** bolt://localhost:7687
- **Default Credentials:** neo4j / (password from .env)

## Production Deployment Options

### Basic Deployment (Neo4j Only)

```bash
docker-compose up -d
```

### With Nginx Reverse Proxy

```bash
docker-compose --profile with-proxy up -d
```

### With Full Monitoring Stack

```bash
docker-compose --profile with-monitoring up -d
```

### All Services

```bash
docker-compose --profile with-proxy --profile with-monitoring up -d
```

## Configuration

### Memory Tuning

Edit `.env` based on available server resources:

```env
# For 8GB server
NEO4J_HEAP_INITIAL=2G
NEO4J_HEAP_MAX=4G
NEO4J_PAGECACHE=2G

# For 16GB server
NEO4J_HEAP_INITIAL=4G
NEO4J_HEAP_MAX=8G
NEO4J_PAGECACHE=4G
```

### Security Hardening

1. **Change Default Password:**
   ```bash
   # In .env
   NEO4J_PASSWORD=your_strong_password_here
   ```

2. **Enable SSL/TLS:**
   - Place certificates in `config/ssl/`
   - Update `config/neo4j.conf` with SSL settings

3. **Firewall Configuration:**
   ```bash
   # Allow only necessary ports
   ufw allow 7474/tcp  # HTTP
   ufw allow 7473/tcp  # HTTPS
   ufw allow 7687/tcp  # Bolt
   ```

4. **Network Isolation:**
   - Use Docker networks
   - Expose only required ports
   - Consider using a reverse proxy

### Backup and Recovery

#### Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec knowledge-graph-neo4j neo4j-admin database dump neo4j \
  --to-path=/data/backups/backup_${DATE}.dump
EOF

chmod +x backup.sh

# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

#### Manual Backup

```bash
# Stop Neo4j
docker-compose stop neo4j

# Create backup
docker run --rm \
  -v neo4j_data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:5.15.0-enterprise \
  neo4j-admin database dump neo4j --to-path=/backups/manual_backup.dump

# Restart Neo4j
docker-compose start neo4j
```

#### Restore from Backup

```bash
# Stop Neo4j
docker-compose stop neo4j

# Restore backup
docker run --rm \
  -v neo4j_data:/data \
  -v $(pwd)/backups:/backups \
  neo4j:5.15.0-enterprise \
  neo4j-admin database load neo4j --from-path=/backups/manual_backup.dump --overwrite-destination=true

# Start Neo4j
docker-compose start neo4j
```

## Monitoring

### Health Checks

```bash
# Check container health
docker-compose ps

# Check Neo4j status
curl http://localhost:7474/

# Check Bolt connectivity
docker exec knowledge-graph-neo4j cypher-shell -u neo4j -p your_password "RETURN 'connected' as status;"
```

### Prometheus Metrics

When using `--profile with-monitoring`:

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)

Neo4j metrics are available at: http://localhost:7474/metrics

### Logs

```bash
# Follow logs
docker-compose logs -f neo4j

# Last 100 lines
docker-compose logs --tail=100 neo4j

# Export logs
docker-compose logs neo4j > neo4j.log
```

## Performance Tuning

### Query Performance

```cypher
// Enable query logging
CALL dbms.setConfigValue('dbms.logs.query.enabled', 'INFO');
CALL dbms.setConfigValue('dbms.logs.query.threshold', '5s');

// Monitor slow queries
// Check /logs/query.log
```

### Index Management

```cypher
// Create indexes for common queries
CREATE INDEX user_email IF NOT EXISTS FOR (u:User) ON (u.email);
CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.id);

// Show all indexes
SHOW INDEXES;

// Monitor index usage
CALL db.stats.retrieve('QUERIES');
```

### Memory Usage

```cypher
// Check memory usage
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Memory Pools') 
YIELD attributes 
RETURN attributes.HeapMemoryUsage.value.used as HeapUsed,
       attributes.HeapMemoryUsage.value.max as HeapMax;
```

## Scaling

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '8'
      memory: 16G
    reservations:
      cpus: '4'
      memory: 8G
```

### Horizontal Scaling (Cluster)

For high availability, consider Neo4j Causal Cluster:
- Requires Neo4j Enterprise Edition
- Minimum 3 core servers
- Configure cluster in `docker-compose.yml`

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs neo4j

# Check permissions
docker-compose exec neo4j ls -la /data

# Reset and restart
docker-compose down
docker volume rm neo4j_data
docker-compose up -d
```

### Out of Memory

```bash
# Increase heap size in .env
NEO4J_HEAP_MAX=4G

# Restart
docker-compose restart neo4j
```

### Connection Refused

```bash
# Check if service is running
docker-compose ps

# Check network
docker network inspect knowledge-graph-network

# Check firewall
sudo ufw status

# Test connectivity
telnet localhost 7687
```

### Slow Queries

```cypher
// Analyze query plan
EXPLAIN MATCH (n:User) WHERE n.email = 'test@example.com' RETURN n;
PROFILE MATCH (n:User) WHERE n.email = 'test@example.com' RETURN n;

// Create missing indexes
CREATE INDEX IF NOT EXISTS FOR (n:User) ON (n.email);
```

## Maintenance

### Updates

```bash
# Pull latest image
docker-compose pull neo4j

# Backup first!
./backup.sh

# Recreate container
docker-compose up -d --force-recreate neo4j
```

### Cleanup

```bash
# Remove old logs (older than 7 days)
docker exec knowledge-graph-neo4j find /logs -name "*.log" -mtime +7 -delete

# Remove old backups
find ./backups -name "*.dump" -mtime +30 -delete

# Prune unused Docker resources
docker system prune -a --volumes
```

## Security Checklist

- [ ] Changed default password
- [ ] Enabled SSL/TLS
- [ ] Configured firewall rules
- [ ] Set up automated backups
- [ ] Enabled query logging
- [ ] Configured resource limits
- [ ] Set up monitoring and alerts
- [ ] Restricted network access
- [ ] Regular security updates
- [ ] Audit logs enabled

## Support

For issues and questions:
- Neo4j Documentation: https://neo4j.com/docs/
- Neo4j Community: https://community.neo4j.com/
- GitHub Issues: [Your repository URL]

## License

Neo4j Enterprise Edition requires a valid license.
See: https://neo4j.com/licensing/
