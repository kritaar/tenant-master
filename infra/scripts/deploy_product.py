#!/usr/bin/env python
"""
Script para desplegar un producto desde su template
Se ejecuta cuando se crea un nuevo workspace

Uso:
    python deploy_product.py --workspace-id 1
"""

import os
import sys
import shutil
import secrets
import string
from pathlib import Path
from jinja2 import Template

# Agregar el path del proyecto
sys.path.append('/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from panel.models import Tenant, Deployment, Product
from django.conf import settings


def generate_password(length=32):
    """Genera una contraseña segura"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secret_key():
    """Genera un secret key de Django"""
    return secrets.token_urlsafe(50)


def render_template(template_str, context):
    """Renderiza un template con Jinja2"""
    template = Template(template_str)
    return template.render(**context)


def deploy_product(workspace_id):
    """
    Despliega un producto para un workspace
    
    Args:
        workspace_id: ID del workspace/tenant
    """
    
    print(f"🚀 Iniciando despliegue para workspace ID: {workspace_id}")
    
    # 1. Obtener el workspace
    try:
        tenant = Tenant.objects.get(id=workspace_id)
        print(f"✅ Workspace encontrado: {tenant.name}")
    except Tenant.DoesNotExist:
        print(f"❌ Error: Workspace {workspace_id} no existe")
        return False
    
    product = tenant.product
    print(f"📦 Producto: {product.display_name}")
    
    # 2. Determinar tipo de deployment
    if tenant.deployment.deployment_type == 'SHARED':
        print(f"🔗 Usando deployment compartido: {tenant.deployment.name}")
        return True  # Ya está desplegado
    
    # 3. Para DEDICATED, crear nuevo deployment
    print("🏗️  Creando deployment dedicado...")
    
    # Paths
    template_path = Path(settings.BASE_DIR).parent / 'infra' / 'deployments' / product.template_path
    deployment_path = Path('/var/deployments') / f"{product.name.lower()}-{tenant.schema_name}"
    
    if not template_path.exists():
        print(f"❌ Error: Template no existe en {template_path}")
        return False
    
    # 4. Copiar template
    print(f"📁 Copiando template desde {template_path}")
    if deployment_path.exists():
        print(f"⚠️  Deployment ya existe en {deployment_path}, eliminando...")
        shutil.rmtree(deployment_path)
    
    shutil.copytree(template_path, deployment_path)
    print(f"✅ Template copiado a {deployment_path}")
    
    # 5. Generar credenciales
    db_password = generate_password()
    secret_key = generate_secret_key()
    
    # 6. Preparar contexto para templates
    context = {
        'WORKSPACE_NAME': tenant.name,
        'SCHEMA_NAME': tenant.schema_name,
        'SUBDOMAIN': tenant.subdomain,
        'BASE_DOMAIN': settings.BASE_DOMAIN,
        'DB_NAME': tenant.db_name,
        'DB_USER': tenant.db_user,
        'DB_PASSWORD': db_password,
        'SECRET_KEY': secret_key,
        'TENANT_SCHEMA': tenant.schema_name,
    }
    
    # 7. Renderizar .env
    env_template_path = deployment_path / '.env.template'
    env_path = deployment_path / '.env'
    
    if env_template_path.exists():
        with open(env_template_path, 'r') as f:
            env_template = f.read()
        
        env_content = render_template(env_template, context)
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Archivo .env creado")
    
    # 8. Renderizar docker-compose.yml
    compose_path = deployment_path / 'docker-compose.yml'
    if compose_path.exists():
        with open(compose_path, 'r') as f:
            compose_content = f.read()
        
        # Reemplazar variables en docker-compose
        for key, value in context.items():
            compose_content = compose_content.replace(f"${{{key}}}", str(value))
        
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        print(f"✅ docker-compose.yml procesado")
    
    # 9. Actualizar tenant con credenciales
    tenant.db_password = db_password
    tenant.save()
    
    # 10. Actualizar deployment
    deployment = tenant.deployment
    deployment.physical_path = str(deployment_path)
    deployment.docker_compose_content = compose_content
    deployment.status = 'ACTIVE'
    deployment.save()
    
    print(f"✅ Deployment actualizado en base de datos")
    
    # 11. Ejecutar docker-compose
    print("🐳 Levantando stack con docker-compose...")
    
    os.chdir(deployment_path)
    result = os.system('docker-compose up -d')
    
    if result == 0:
        print("✅ Stack levantado exitosamente")
        
        # Log de actividad
        from panel.models import ActivityLog
        ActivityLog.objects.create(
            tenant=tenant,
            deployment=deployment,
            user=tenant.owner,
            action='deploy',
            description=f"Deployment {deployment.name} creado exitosamente"
        )
        
        print(f"\n🎉 ¡Despliegue completado!")
        print(f"🌐 URL: {tenant.url}")
        print(f"📁 Path: {deployment_path}")
        
        return True
    else:
        print("❌ Error al levantar el stack")
        deployment.status = 'ERROR'
        deployment.error_message = "Error al ejecutar docker-compose up"
        deployment.save()
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Desplegar producto para workspace')
    parser.add_argument('--workspace-id', type=int, required=True, help='ID del workspace')
    
    args = parser.parse_args()
    
    success = deploy_product(args.workspace_id)
    sys.exit(0 if success else 1)
