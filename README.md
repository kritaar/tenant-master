# Tenant Master

Panel de administración para gestión de workspaces multi-tenant.

## 🚀 Características

- ✅ Registro de usuarios y workspaces
- ✅ Gestión de múltiples productos (Inventario, ERP, Tienda, Web)
- ✅ Creación automática de bases de datos por tenant
- ✅ Sistema de membresías (Owner, Admin, Member)
- ✅ Dashboard con vista de todos los workspaces
- ✅ Integración con PostgreSQL multi-tenant

## 🏗️ Arquitectura

```
tenant-master/
├── backend/
│   ├── config/          # Configuración Django
│   ├── accounts/        # App principal (workspaces)
│   ├── templates/       # Templates HTML
│   └── static/          # CSS/JS
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🐳 Despliegue

### Con Docker Compose

```bash
docker-compose up -d
```

### Con Portainer (GitOps)

1. Crear stack en Portainer
2. Repository: `https://github.com/kritaar/tenant-master`
3. Compose path: `docker-compose.yml`
4. GitOps updates: ON
5. Deploy

## 🔧 Configuración

Variables de entorno (ver `.env.example`):

```env
DJANGO_SECRET_KEY=your-secret-key
PGHOST=postgres16
PGDATABASE=tenant_master
PGUSER=admin
PGPASSWORD=1234
TENANT_DOMAIN=kitagli.com
```

## 📋 Requisitos

- PostgreSQL 16 (contenedor `postgres16`)
- Red Docker: `tenant-network`
- Script de creación de tenants: `/opt/databases/postgresql/create_tenant.sh`

## 🌐 URLs

- Panel admin: `https://app.kitagli.com`
- Django admin: `https://app.kitagli.com/admin`

## 📝 Desarrollo Local

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## 🔗 Productos Disponibles

- **Inventario** - Sistema de gestión de inventario
- **ERP** - Sistema de planificación empresarial
- **Shop** - Tienda virtual
- **Web** - Constructor de sitios web

## 📄 Licencia

Privado - Todos los derechos reservados
