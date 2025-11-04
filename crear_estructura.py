import os
import shutil

BASE = r"C:\Proyectos_vps\tenant_master"

FILE_MAP = {
    "app-backend-Dockerfile": "app/backend/Dockerfile",
    "app-backend-requirements.txt": "app/backend/requirements.txt",
    "app-backend-manage.py": "app/backend/manage.py",
    "app-backend-config-__init__.py": "app/backend/config/__init__.py",
    "app-backend-config-settings.py": "app/backend/config/settings.py",
    "app-backend-config-urls.py": "app/backend/config/urls.py",
    "app-backend-config-wsgi.py": "app/backend/config/wsgi.py",
    "app-backend-panel-__init__.py": "app/backend/panel/__init__.py",
    "app-backend-panel-apps.py": "app/backend/panel/apps.py",
    "app-backend-panel-models.py": "app/backend/panel/models.py",
    "app-backend-panel-admin.py": "app/backend/panel/admin.py",
    "app-backend-panel-views.py": "app/backend/panel/views.py",
    "app-backend-panel-urls.py": "app/backend/panel/urls.py",
    "app-backend-panel-middleware.py": "app/backend/panel/middleware.py",
    "app-backend-panel-routers.py": "app/backend/panel/routers.py",
    "app-backend-panel-api-__init__.py": "app/backend/panel/api/__init__.py",
    "app-backend-panel-api-urls.py": "app/backend/panel/api/urls.py",
    "app-backend-panel-api-views.py": "app/backend/panel/api/views.py",
    "app-backend-panel-api-serializers.py": "app/backend/panel/api/serializers.py",
    "app-backend-panel-templates-panel-base.html": "app/backend/panel/templates/panel/base.html",
    "app-backend-panel-templates-panel-login.html": "app/backend/panel/templates/panel/login.html",
    "app-backend-panel-templates-panel-dashboard.html": "app/backend/panel/templates/panel/dashboard.html",
    "app-backend-panel-templates-panel-workspaces.html": "app/backend/panel/templates/panel/workspaces.html",
    "app-backend-panel-templates-panel-create_workspace.html": "app/backend/panel/templates/panel/create_workspace.html",
    "infra-core-docker-compose.yml": "infra/core/docker-compose.yml",
    "infra-core-env-example.txt": "infra/core/.env.example",
    "infra-core-postgres-gitkeep.txt": "infra/core/postgres/.gitkeep",
    "infra-deployments-README.md": "infra/deployments/README.md",
    "infra-deployments-TEMPLATE-docker-compose.yml": "infra/deployments/TEMPLATE/docker-compose.yml",
    "infra-deployments-TEMPLATE-env-example.txt": "infra/deployments/TEMPLATE/.env.example",
    "infra-deployments-TEMPLATE-postgres-gitkeep.txt": "infra/deployments/TEMPLATE/postgres/.gitkeep",
    "infra-scripts-provision_tenant.py": "infra/scripts/provision_tenant.py",
    "infra-scripts-migrate_all.py": "infra/scripts/migrate_all.py",
    "infra-scripts-backup.sh": "infra/scripts/backup.sh",
}

print("Organizando archivos...")

for source, dest in FILE_MAP.items():
    source_path = os.path.join(BASE, source)
    dest_path = os.path.join(BASE, dest)
    
    if os.path.exists(source_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(source_path, dest_path)
        print(f"✓ {source} -> {dest}")
    else:
        print(f"✗ {source} no encontrado")

print("\n✅ Estructura organizada!")
print("\nAhora crea los templates restantes en:")
print("app/backend/panel/templates/panel/")
print("\nTemplates faltantes:")
print("- workspace_detail.html")
print("- clients.html") 
print("- deployments.html")
print("- products.html")
print("- databases.html")
print("- activity.html")
print("- settings.html")
print("\nEl contenido está en: app-backend-panel-templates-panel-ALL-REMAINING.txt")