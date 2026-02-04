#!/bin/bash
set -e

echo "======================================"
echo "  GiHaNotis Docker Entrypoint"
echo "======================================"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✓ PostgreSQL is ready!"

# Check if database schema is loaded
echo "Checking database schema..."
TABLE_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -lt 2 ]; then
    echo "Loading database schema..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f schema.sql
    echo "✓ Database schema loaded"
else
    echo "✓ Database schema already exists"
fi

echo ""
echo "======================================"
echo "  Starting GiHaNotis Application"
echo "======================================"
echo "Environment: $FLASK_ENV"
echo "Database: $DB_NAME@$DB_HOST"
echo "Admin username: $ADMIN_USERNAME"
echo "======================================"
echo ""

# Execute the main command
exec "$@"
