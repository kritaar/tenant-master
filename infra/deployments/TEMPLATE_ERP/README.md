# Template: Sistema ERP

Este es el template base para desplegar el Sistema ERP en cada workspace.

## 🎯 Propósito

Este template es usado por `tenant-master` para crear instancias del Sistema ERP para cada cliente.

## 📁 Estructura

```
TEMPLATE_ERP/
├── docker-compose.yml      # Stack del ERP
├── .env.template           # Variables de entorno (con placeholders)
├── init.sql                # Datos iniciales
├── postgres/               # Datos de PostgreSQL (vacío inicialmente)
└── README.md              # Este archivo
```

## 🔄 Proceso de Despliegue

Cuando un usuario crea un workspace con el producto "Sistema ERP":

1. **Tenant Master** copia este template a `/var/deployments/erp-{schema_name}/`
2. Reemplaza los placeholders en `.env.template`:
   - `{{WORKSPACE_NAME}}` → Nombre del workspace
   - `{{SCHEMA_NAME}}` → Schema único del tenant
   - `{{SUBDOMAIN}}` → Subdominio asignado
   - `{{DB_NAME}}` → Nombre de la base de datos
   - `{{DB_USER}}` → Usuario de la base de datos
   - `{{DB_PASSWORD}}` → Contraseña generada
   - `{{SECRET_KEY}}` → Secret key de Django
3. Crea el stack en Portainer o ejecuta `docker-compose up -d`
4. El backend ejecuta migraciones automáticamente
5. PostgreSQL ejecuta `init.sql` con datos de ejemplo
6. Traefik configura el certificado SSL
7. El ERP queda disponible en `https://{subdomain}.surgir.online`

## 🚀 Despliegue Manual (para desarrollo)

```bash
# Copiar template
cp -r TEMPLATE_ERP ../mi-tenant-test

# Crear .env manualmente
cd ../mi-tenant-test
cp .env.template .env

# Editar variables
nano .env

# Levantar
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

## 📊 Características del ERP

- ✅ Gestión de productos con control de inventario
- ✅ Clientes y proveedores
- ✅ Compras y ventas
- ✅ Control de lotes y series
- ✅ Movimientos de inventario
- ✅ Dashboard con estadísticas
- ✅ API REST completa
- ✅ Frontend React responsive

## 🔧 Mantenimiento

### Actualizar la imagen del backend
```bash
docker pull ghcr.io/tenant-master/erp-backend:latest
docker-compose up -d backend
```

### Actualizar la imagen del frontend
```bash
docker pull ghcr.io/tenant-master/erp-frontend:latest
docker-compose up -d frontend
```

### Backup de la base de datos
```bash
docker exec erp-{schema}-db pg_dump -U {db_user} {db_name} > backup.sql
```

### Restaurar backup
```bash
cat backup.sql | docker exec -i erp-{schema}-db psql -U {db_user} {db_name}
```

## 📝 Notas

- Las imágenes Docker deben estar en un registry accesible
- El network `tenant-network` debe existir previamente
- Traefik debe estar configurado como proxy inverso
- Los certificados SSL se generan automáticamente con Let's Encrypt
