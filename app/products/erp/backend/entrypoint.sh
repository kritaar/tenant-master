#!/bin/bash
set -e

echo "🔄 Waiting for PostgreSQL..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "✅ PostgreSQL is ready"

echo "🔄 Running migrations..."
python manage.py migrate --noinput

echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput

echo "🔄 Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@erp.com', 'admin123')
    print('✅ Superuser created')
else:
    print('ℹ️ Superuser already exists')
END

echo "🚀 Starting application..."
exec "$@"
