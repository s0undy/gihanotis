#!/bin/bash

# GiHaNotis Setup Script
# This script helps set up the GiHaNotis application

set -e

echo "======================================"
echo "  GiHaNotis Setup Script"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env

    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Update SECRET_KEY in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-key-change-this-in-production/$SECRET_KEY/" .env
    fi

    echo "✓ Created .env file with random SECRET_KEY"
    echo ""
    echo "IMPORTANT: Please edit .env and configure:"
    echo "  - Database credentials (DB_PASSWORD, DB_USER)"
    echo "  - Admin credentials (ADMIN_USERNAME, ADMIN_PASSWORD)"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 is installed: $(python3 --version)"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "⚠ PostgreSQL client not found. Please ensure PostgreSQL is installed."
    echo ""
else
    echo "✓ PostgreSQL client is installed: $(psql --version)"
    echo ""
fi

# Ask if user wants to create virtual environment
read -p "Create a Python virtual environment? (recommended) [Y/n]: " create_venv
create_venv=${create_venv:-Y}

if [[ $create_venv =~ ^[Yy]$ ]]; then
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
        echo "✓ Virtual environment created"
        echo ""
        echo "To activate it, run:"
        echo "  source venv/bin/activate"
        echo ""
    else
        echo "✓ Virtual environment already exists"
        echo ""
    fi
fi

# Ask if user wants to install dependencies
read -p "Install Python dependencies? [Y/n]: " install_deps
install_deps=${install_deps:-Y}

if [[ $install_deps =~ ^[Yy]$ ]]; then
    echo "Installing dependencies..."

    # Check if venv is activated
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        pip install -r requirements.txt
    else
        python3 -m pip install -r requirements.txt
    fi

    echo "✓ Dependencies installed"
    echo ""
fi

# Ask if user wants to set up database
read -p "Set up PostgreSQL database? (requires PostgreSQL access) [y/N]: " setup_db
setup_db=${setup_db:-N}

if [[ $setup_db =~ ^[Yy]$ ]]; then
    echo ""
    echo "Database setup requires PostgreSQL credentials."
    read -p "PostgreSQL admin username [postgres]: " pg_user
    pg_user=${pg_user:-postgres}

    read -p "Database name [gihanotis]: " db_name
    db_name=${db_name:-gihanotis}

    read -p "Database user [gihanotis_user]: " db_user
    db_user=${db_user:-gihanotis_user}

    read -sp "Database password for $db_user: " db_pass
    echo ""

    # Create database and user
    echo "Creating database..."
    sudo -u $pg_user psql -c "CREATE DATABASE $db_name;" 2>/dev/null || echo "Database may already exist"
    sudo -u $pg_user psql -c "CREATE USER $db_user WITH PASSWORD '$db_pass';" 2>/dev/null || echo "User may already exist"
    sudo -u $pg_user psql -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"

    # Load schema
    echo "Loading database schema..."
    PGPASSWORD=$db_pass psql -U $db_user -d $db_name -f schema.sql

    echo "✓ Database setup complete"
    echo ""
fi

echo "======================================"
echo "  Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your configuration"
echo "2. Activate virtual environment (if created):"
echo "     source venv/bin/activate"
echo ""
echo "3. Run the application:"
echo "     python3 app.py"
echo ""
echo "4. Access the application:"
echo "     Public:  http://localhost:5000/"
echo "     Admin:   http://localhost:5000/admin"
echo ""
echo "For more information, see README.md"
echo ""
