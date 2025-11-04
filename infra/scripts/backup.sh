#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_USER=${POSTGRES_USER:-tenant_admin}

mkdir -p $BACKUP_DIR

echo "Starting backup process..."

pg_dump -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d tenant_master > "$BACKUP_DIR/tenant_master_$DATE.sql"
echo "✓ Master database backed up"

TENANT_DBS=$(psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d tenant_master -t -c "SELECT db_name FROM panel_tenant WHERE status='active'")

for db in $TENANT_DBS; do
    if [ ! -z "$db" ]; then
        pg_dump -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $db > "$BACKUP_DIR/${db}_$DATE.sql"
        echo "✓ $db backed up"
    fi
done

find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
echo "✓ Old backups cleaned (>7 days)"

echo "Backup completed successfully!"
