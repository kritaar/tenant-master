#!/usr/bin/env python3
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess

def create_tenant_database(tenant_name, db_name):
    master_conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'tenant_admin'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database='postgres'
    )
    master_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = master_conn.cursor()
    
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"Database {db_name} created successfully")
    else:
        print(f"Database {db_name} already exists")
    
    cursor.close()
    master_conn.close()

def run_migrations(db_name):
    env = os.environ.copy()
    env['DATABASE_NAME'] = db_name
    
    result = subprocess.run(
        ['python', 'manage.py', 'migrate', '--database', db_name],
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"Migrations applied successfully to {db_name}")
    else:
        print(f"Error applying migrations: {result.stderr}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: provision_tenant.py <tenant_name> <db_name>")
        sys.exit(1)
    
    tenant_name = sys.argv[1]
    db_name = sys.argv[2]
    
    print(f"Provisioning tenant: {tenant_name}")
    print(f"Database name: {db_name}")
    
    create_tenant_database(tenant_name, db_name)
    run_migrations(db_name)
    
    print(f"Tenant {tenant_name} provisioned successfully!")
    print(f"Database: {db_name}")

if __name__ == '__main__':
    main()
