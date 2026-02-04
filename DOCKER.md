# Docker Deployment Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Generate SECRET_KEY and update .env
python3 -c "import secrets; print(secrets.token_hex(32))"
nano .env  # Set SECRET_KEY, DB_PASSWORD, ADMIN_PASSWORD

# 3. Start services
docker-compose up -d

# 4. Access application
# Public:  http://localhost:5000/
# Admin:   http://localhost:5000/admin
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

### 2. Use Gunicorn

Add to Dockerfile:
```dockerfile
RUN pip install gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### 3. Add Nginx (Optional)

For HTTPS and better performance, add nginx as a reverse proxy.

## Troubleshooting

### Container Won't Start

```bash
docker-compose logs web
docker-compose exec web env | grep DB_
```

### Database Connection Error

```bash
docker-compose ps db
docker-compose exec db pg_isready -U gihanotis_user
```

### Port Already in Use

```bash
sudo lsof -i :5000
# Or change port in docker-compose.yml:
# ports: ["8080:5000"]
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
# Application health endpoint
curl http://localhost:5000/health
# Response: {"status": "ok", "database": "connected"}

# Database health
docker-compose exec db pg_isready -U gihanotis_user

# API Documentation
# Open http://localhost:5000/docs in browser
```
