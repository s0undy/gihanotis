# GiHaNotis - Crisis Resource Inventory System

A simple, API-first web application for managing resource requests and responses during crisis situations. Built with Flask and PostgreSQL following KISS (Keep It Simple, Stupid) principles.

## Overview

GiHaNotis allows administrators to create resource requests (e.g., "need 5 shovels") and enables community members to respond with available quantities and locations. The system provides two separate interfaces:

- **Admin Interface**: Create, manage, and track resource requests and view all responses
- **Public Interface**: View open requests and submit responses with location information

## Features

- Simple authentication for admin users
- RESTful API design
- Server-side rendered HTML templates
- Real-time request and response management
- Location tracking for available resources
- Optional responder contact information
- Request status management (open/closed)
- Responsive Bootstrap 5 UI
- **Rate limiting** on login (5 attempts/minute)
- **Session timeout** (8 hours)
- **CSRF protection** for forms
- **Pagination** on list endpoints
- **Health check endpoint** at `/health`
- **API documentation** at `/docs` (Scalar UI)

## Technology Stack

- **Backend**: Python 3.8+ with Flask 3.0
- **Database**: PostgreSQL 12+
- **Frontend**: Jinja2 templates with Bootstrap 5
- **Database Driver**: psycopg2 (raw SQL queries, no ORM)
- **Rate Limiting**: Flask-Limiter
- **CSRF Protection**: Flask-WTF
- **API Docs**: Scalar (OpenAPI 3.0)
- **Deployment**: Docker and Docker Compose support

## Quick Start with Docker

The easiest way to run GiHaNotis is with Docker:

```bash
# 1. Create environment file
cp .env.example .env

# 2. Generate secure SECRET_KEY and edit .env
python3 -c "import secrets; print(secrets.token_hex(32))"
nano .env  # Set SECRET_KEY, DB_PASSWORD, ADMIN_PASSWORD

# 3. Start all services
docker-compose up -d

# 4. Access the application
# Public:  http://localhost:5000/
# Admin:   http://localhost:5000/admin
```

See [DOCKER.md](DOCKER.md) for database backup/restore and production deployment.

## Project Structure

```
GiHaNotis/
├── app.py              # Main Flask application
├── config.py           # Configuration management
├── db.py               # Database connection helpers
├── validation.py       # Input validation
├── requirements.txt    # Python dependencies
├── schema.sql          # Database schema
├── .env.example        # Environment template
├── templates/          # Jinja2 templates
│   ├── base.html
│   ├── admin/          # Admin interface
│   └── public/         # Public interface
└── static/css/         # Stylesheets
```

## Setup Instructions (Native Installation)

For Docker installation, see [Quick Start with Docker](#quick-start-with-docker) above or [DOCKER.md](DOCKER.md).

### 1. Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package installer)

### 2. Clone or Navigate to Project

```bash
cd /home/ant057/KLIRR/GiHaNotis
```

### 3. Install Python Dependencies

```bash
# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```bash
# Create database
sudo -u postgres psql
postgres=# CREATE DATABASE gihanotis;
postgres=# CREATE USER gihanotis_user WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE gihanotis TO gihanotis_user;
postgres=# \q

# Load schema
psql -U gihanotis_user -d gihanotis -f schema.sql
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Database Configuration
DB_HOST=localhost
DB_NAME=gihanotis
DB_USER=gihanotis_user
DB_PASSWORD=your_secure_password

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password

# Flask Configuration
SECRET_KEY=generate-a-random-secret-key-here
FLASK_ENV=development
```

**Important**: Generate a secure SECRET_KEY:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 6. Run the Application

```bash
python3 app.py
```

The application will start on `http://localhost:5000`

- **Public Interface**: http://localhost:5000/
- **Admin Interface**: http://localhost:5000/admin

## Usage Guide

### Admin Workflow

1. Navigate to http://localhost:5000/admin
2. Login with credentials from `.env`
3. Create a new request:
   - Enter item name (e.g., "Shovels")
   - Enter quantity needed (e.g., 5)
   - Enter unit (e.g., "pieces")
   - Optionally add description
4. View all requests in the dashboard
5. Click "View Details" to see responses
6. Close or delete requests as needed

### Public Workflow

1. Navigate to http://localhost:5000/
2. Browse open resource requests
3. Click "I Can Help" on a request
4. Fill out response form:
   - Quantity available (required)
   - Location (required)
   - Name (optional)
   - Contact info (optional)
   - Additional notes (optional)
5. Submit response
6. Admin will see your response

## API Documentation

### Authentication Endpoints

#### POST /api/auth/login
Login as admin.

**Request:**
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful"
}
```

#### POST /api/auth/logout
Logout admin session.

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Admin Endpoints (Requires Authentication)

#### GET /api/requests
List all requests with response counts.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "item_name": "Shovels",
      "quantity_needed": 5,
      "unit": "pieces",
      "description": "For debris removal",
      "status": "open",
      "created_at": "2026-02-04T10:00:00",
      "response_count": 3
    }
  ]
}
```

#### POST /api/requests
Create a new request.

**Request:**
```json
{
  "item_name": "Shovels",
  "quantity_needed": 5,
  "unit": "pieces",
  "description": "For debris removal"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "item_name": "Shovels",
    "quantity_needed": 5,
    "unit": "pieces",
    "description": "For debris removal",
    "status": "open",
    "created_at": "2026-02-04T10:00:00"
  }
}
```

#### GET /api/requests/{id}
Get a single request with all responses.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "item_name": "Shovels",
    "quantity_needed": 5,
    "unit": "pieces",
    "description": "For debris removal",
    "status": "open",
    "created_at": "2026-02-04T10:00:00",
    "responses": [
      {
        "id": 1,
        "responder_name": "John Doe",
        "responder_contact": "john@example.com",
        "quantity_available": 2,
        "location": "123 Main St",
        "notes": "Can deliver tomorrow",
        "created_at": "2026-02-04T11:00:00"
      }
    ]
  }
}
```

#### PUT /api/requests/{id}
Update a request (e.g., change status).

**Request:**
```json
{
  "status": "closed"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "closed",
    ...
  }
}
```

#### DELETE /api/requests/{id}
Delete a request.

**Response:**
```json
{
  "success": true,
  "message": "Request deleted"
}
```

### Public Endpoints (No Authentication)

#### GET /api/public/requests
List all open requests.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "item_name": "Shovels",
      "quantity_needed": 5,
      "unit": "pieces",
      "description": "For debris removal",
      "created_at": "2026-02-04T10:00:00"
    }
  ]
}
```

#### GET /api/public/requests/{id}
Get a single open request.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "item_name": "Shovels",
    "quantity_needed": 5,
    "unit": "pieces",
    "description": "For debris removal",
    "created_at": "2026-02-04T10:00:00"
  }
}
```

#### POST /api/public/requests/{id}/responses
Submit a response to a request.

**Request:**
```json
{
  "quantity_available": 2,
  "location": "123 Main St",
  "responder_name": "John Doe",
  "responder_contact": "john@example.com",
  "notes": "Can deliver tomorrow"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "request_id": 1,
    "quantity_available": 2,
    "location": "123 Main St",
    "responder_name": "John Doe",
    "responder_contact": "john@example.com",
    "notes": "Can deliver tomorrow",
    "created_at": "2026-02-04T11:00:00"
  }
}
```

## Database Schema

### Table: requests

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| item_name | VARCHAR(255) | Name of requested item |
| quantity_needed | INTEGER | Quantity needed |
| unit | VARCHAR(50) | Unit of measurement |
| description | TEXT | Optional description |
| status | VARCHAR(20) | 'open' or 'closed' |
| created_at | TIMESTAMP | Creation timestamp |

### Table: responses

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL PRIMARY KEY | Unique identifier |
| request_id | INTEGER | Foreign key to requests |
| responder_name | VARCHAR(255) | Optional responder name |
| responder_contact | VARCHAR(255) | Optional contact info |
| quantity_available | INTEGER | Quantity available |
| location | VARCHAR(500) | Location of resource |
| notes | TEXT | Optional additional notes |
| created_at | TIMESTAMP | Submission timestamp |

## Testing

### Manual Testing

1. **Test Admin Login**:
   ```bash
   curl -X POST http://localhost:5000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your_password"}'
   ```

2. **Test Create Request**:
   ```bash
   curl -X POST http://localhost:5000/api/requests \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"item_name":"Shovels","quantity_needed":5,"unit":"pieces"}'
   ```

3. **Test Public View**:
   ```bash
   curl http://localhost:5000/api/public/requests
   ```

4. **Test Submit Response**:
   ```bash
   curl -X POST http://localhost:5000/api/public/requests/1/responses \
     -H "Content-Type: application/json" \
     -d '{"quantity_available":2,"location":"123 Main St"}'
   ```

### Browser Testing

1. Navigate to http://localhost:5000
2. Verify public request list displays
3. Click "I Can Help" and submit response
4. Navigate to http://localhost:5000/admin
5. Login with admin credentials
6. Create a new request
7. View request details and verify responses appear

## Security Considerations

- **SQL Injection**: All queries use parameterized statements
- **XSS**: Jinja2 auto-escapes + input sanitization via `sanitize_html()`
- **CSRF**: Flask-WTF CSRFProtect with token validation
- **Rate Limiting**: Login endpoint limited to 5 attempts/minute/IP
- **Session Security**:
  - HttpOnly cookies
  - SameSite=Lax
  - 8-hour automatic timeout
- **Input Validation**: All text inputs sanitized before storage
- **Authentication**: Session-based admin authentication
- **Passwords**: Store securely in .env

## API Documentation

Interactive API documentation is available at:
- **Scalar UI**: http://localhost:5000/docs
- **OpenAPI Spec**: http://localhost:5000/static/openapi.json

## Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Generate a strong SECRET_KEY
3. Use a production WSGI server (gunicorn, uwsgi)
4. Set up nginx as reverse proxy
5. Enable HTTPS
6. Set `SESSION_COOKIE_SECURE=True` in config.py
7. Configure PostgreSQL with proper access controls

### Example with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Database Connection Error

- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check credentials in `.env`
- Verify database exists: `psql -U postgres -c "\l"`

### Import Errors

- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Permission Errors

- Check database user permissions
- Verify .env file has correct permissions: `chmod 600 .env`

## Contributing

This is a simple crisis management tool. Contributions are welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is released as open source for crisis response and community support.

## Support

For issues or questions, please check:
- Database connectivity
- Environment configuration
- Console error messages

## Version

Current Version: 1.0.0
Last Updated: 2026-02-04
