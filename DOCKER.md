# Docker Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Architecture

```
                    INTERNET
                        │
                        ▼
               ┌────────────────┐
               │     NGINX      │  ← Only externally accessible (port 80)
               │   (port 80)    │
               └───────┬────────┘
                       │
        ───────────────┼─────────────── internal network
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   ┌──────────────┐         ┌──────────────┐
   │  Flask App   │────────▶│  PostgreSQL  │
   │ (port 5000)  │         │ (port 5432)  │
   │   internal   │         │   internal   │
   └──────────────┘         └──────────────┘
```

**Security:** Flask and PostgreSQL are NOT exposed to the host. Only Nginx (port 80) is accessible externally.

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Generate SECRET_KEY and update .env
python3 -c "import secrets; print(secrets.token_hex(32))"
nano .env  # Set SECRET_KEY, DB_PASSWORD, ADMIN_PASSWORD

# 3. Start services
docker-compose up -d

# 4. Access application (via Nginx)
# Public:  http://localhost/
# Admin:   http://localhost/admin
# Docs:    http://localhost/docs
```

## Common Commands

```bash
# Start/stop
docker-compose up -d
docker-compose stop
docker-compose down      # Stop and remove containers
docker-compose down -v   # Also remove data volume

# View logs
docker-compose logs -f
docker-compose logs -f web
docker-compose logs -f nginx

# Rebuild after code changes
docker-compose up -d --build
```

## Database Management

### Backup

```bash
docker-compose exec db pg_dump -U gihanotis_user gihanotis > backup.sql
```

### Restore

```bash
docker-compose exec -T db psql -U gihanotis_user gihanotis < backup.sql
```

### Reset Database

```bash
docker-compose down -v
docker-compose up -d
```

### Access Database

```bash
docker-compose exec db psql -U gihanotis_user -d gihanotis
```

## Production Deployment

### 1. Update Environment

```env
FLASK_ENV=production
SECRET_KEY=<strong-random-key>
DB_PASSWORD=<strong-password>
ADMIN_PASSWORD=<strong-password>
```

### 2. HTTPS (Optional)

To enable HTTPS, update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}
```

Add SSL volume to docker-compose.yml:
```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
```

## Troubleshooting

### Container Won't Start

```bash
docker-compose logs web
docker-compose logs nginx
docker-compose exec web env | grep DB_
```

### Database Connection Error

```bash
docker-compose ps db
docker-compose exec db pg_isready -U gihanotis_user
```

### Port Already in Use

```bash
sudo lsof -i :80
# Or change port in docker-compose.yml:
# nginx:
#   ports: ["8080:80"]
```

### Permission Errors

```bash
chmod +x docker-entrypoint.sh
docker-compose build --no-cache
```

### Out of Disk Space

```bash
docker system prune -a
docker volume prune
```

## Health Checks

```bash
# Application health endpoint (via Nginx)
curl http://localhost/health
# Response: {"status": "ok", "database": "connected"}

# Check security headers
curl -I http://localhost/ | grep -i "content-security-policy\|x-frame"

# Database health
docker-compose exec db pg_isready -U gihanotis_user

# Container status
docker-compose ps

# API Documentation
# Open http://localhost/docs in browser
```

## Services

| Service | Container | Internal Port | External Port |
|---------|-----------|---------------|---------------|
| Nginx | gihanotis-nginx | 80 | **80** (exposed) |
| Flask | gihanotis-web | 5000 | None (internal) |
| PostgreSQL | gihanotis-db | 5432 | None (internal) |
