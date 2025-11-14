#!/usr/bin/env python3
import os
import sys
import subprocess
import secrets
import string
from pathlib import Path

def generate_password(length=32):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_workspace_deployment(workspace_id):
    sys.path.insert(0, '/app')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    import django
    django.setup()
    
    from panel.models import Tenant
    from django.utils import timezone
    
    tenant = Tenant.objects.get(id=workspace_id)
    
    print(f"🚀 Deploying workspace: {tenant.subdomain}")
    
    project_path = Path(f"/opt/proyectos/{tenant.subdomain}")
    stack_path = Path(f"/opt/stacks/{tenant.subdomain}")
    
    project_path.mkdir(parents=True, exist_ok=True)
    stack_path.mkdir(parents=True, exist_ok=True)
    
    subprocess.run(['git', 'init'], cwd=project_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'TenantMaster'], cwd=project_path, check=True)
    subprocess.run(['git', 'config', 'user.email', 'admin@surgir.online'], cwd=project_path, check=True)
    
    (project_path / 'README.md').write_text(f"# {tenant.company_name}\n\nWorkspace: {tenant.subdomain}")
    
    subprocess.run(['git', 'add', '.'], cwd=project_path, check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_path, check=True)
    subprocess.run(['git', 'branch', '-M', 'main'], cwd=project_path, check=True)
    
    compose_content = f"""version: '3.8'

services:
  {tenant.subdomain}:
    image: {tenant.product.docker_image or 'nginx:alpine'}
    container_name: {tenant.subdomain}
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://{tenant.db_user}:{tenant.db_password}@{tenant.db_host}:{tenant.db_port}/{tenant.db_name}
    volumes:
      - {project_path}:/app:ro
    networks:
      - tenant-master-core_default
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{tenant.subdomain}.rule=Host(`{tenant.subdomain}.surgir.online`)"
      - "traefik.http.routers.{tenant.subdomain}.entrypoints=websecure"
      - "traefik.http.routers.{tenant.subdomain}.tls.certresolver=letsencrypt"

networks:
  tenant-master-core_default:
    external: true
"""
    
    (stack_path / 'docker-compose.yml').write_text(compose_content)
    
    (stack_path / '.env').write_text(f"""WORKSPACE_NAME={tenant.subdomain}
DOMAIN={tenant.subdomain}.surgir.online
DB_NAME={tenant.db_name}
DB_USER={tenant.db_user}
DB_PASSWORD={tenant.db_password}
""")
    
    tenant.project_path = str(project_path)
    tenant.stack_path = str(stack_path)
    tenant.git_repo_url = f"root@srv1099809:{project_path}"
    tenant.is_deployed = True
    tenant.deployed_at = timezone.now()
    tenant.save()
    
    print(f"✅ Deployment complete!")
    print(f"   Project: {project_path}")
    print(f"   Stack: {stack_path}")
    print(f"   Git: {tenant.git_repo_url}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: deploy_workspace.py <workspace_id>")
        sys.exit(1)
    
    create_workspace_deployment(int(sys.argv[1]))
