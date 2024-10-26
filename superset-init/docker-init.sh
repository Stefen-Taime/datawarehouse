#!/bin/bash
set -e

# Wait for superset database to be ready
echo "Waiting for Superset database..."
while ! nc -z superset-db 5432; do
  sleep 1
done
echo "Superset database is ready!"

# Initialize Superset
echo "Initializing Superset..."
superset db upgrade
superset init

# Create admin user
echo "Creating admin user..."
superset fab create-admin \
    --username $SUPERSET_ADMIN_USERNAME \
    --firstname Superset \
    --lastname Admin \
    --email $SUPERSET_ADMIN_EMAIL \
    --password $SUPERSET_ADMIN_PASSWORD

# Create default roles and permissions
echo "Setting up roles and permissions..."
superset init

# Create database connection
echo "Creating database connection..."
superset set-database-uri \
    --database-name "DataWarehouse" \
    --uri "postgresql://admin:adminpassword@warehouse:5432/myapp"

# Import dashboards
echo "Importing dashboards..."
superset import-dashboards --path /app/docker/dashboards.json

echo "Setup completed!"