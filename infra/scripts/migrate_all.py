#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from panel.models import Tenant
import subprocess

def migrate_tenant(tenant):
    print(f"Migrating tenant: {tenant.name} ({tenant.db_name})")
    
    env = os.environ.copy()
    env['DATABASE_NAME'] = tenant.db_name
    
    result = subprocess.run(
        ['python', 'manage.py', 'migrate', '--database', tenant.db_name],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✓ {tenant.name} migrated successfully")
        return True
    else:
        print(f"✗ {tenant.name} migration failed: {result.stderr}")
        return False

def main():
    tenants = Tenant.objects.filter(status='active')
    total = tenants.count()
    success = 0
    failed = 0
    
    print(f"Starting migration for {total} tenants...")
    
    for tenant in tenants:
        if migrate_tenant(tenant):
            success += 1
        else:
            failed += 1
    
    print(f"\nMigration completed:")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total: {total}")

if __name__ == '__main__':
    main()
