# Tenant Master - Multi-Tenant Panel

Sistema multi-tenant con panel de administración, runtime compartido, base de datos por tenant y soporte para deployments dedicados.

## 🏗️ Arquitectura

- **Runtime compartido**: Un solo stack Django sirve múltiples tenants
- **DB por tenant**: Cada cliente tiene su propia base de datos PostgreSQL
- **Deployments dedicados**: Opción de stack completo aislado por cliente
- **SSO maestro**: Login único para administrar todos los tenants
- **Auto-deploy**: Stack desde Git con Portainer

## 🚀 Inicio Rápido

### Pre-requisitos

1. VPS con Docker + Portainer instalado
2. Dominio con DNS configurado:
   - `panel.surgir.online` → IP del VPS
   - `*.surgir.online` → IP del VPS (wildcard)

### Deployment

1. **Clonar este repositorio**

2. **En Portainer:**
   - Ir a **Stacks** → **Add Stack**
   - Seleccionar **Repository**
   - Repository URL: `https://github.com/kritaar/tenant_master`
   - Compose path: `infra/core/docker-compose.yml`
   - Auto update: ✅ Activar

3. **Configurar variables de entorno** (copiar de `infra/core/.env.example`):
   ```env
   LE_EMAIL=admin@surgir.online
   PANEL_DOMAIN=panel.surgir.online
   BASE_DOMAIN=surgir.online
   POSTGRES_PASSWORD=tu_password_seguro
   DJANGO_SECRET_KEY=tu_secret_key_aleatorio
   MASTER_USERNAME=admin
   PORTAINER_BASE=http://portainer:9000
   PORTAINER_API_KEY=tu_api_key
   ```

4. **Deploy** y esperar 2-3 minutos

5. **Acceder al panel:**
   ```
   https://panel.surgir.online
   ```

### Primer uso

1. Crear superusuario:
   ```bash
   docker exec -it tenant-master-panel python manage.py createsuperuser
   ```

2. Acceder al panel con las credenciales creadas

3. Ya puedes crear workspaces desde el panel

## 📦 Estructura del Proyecto

```
tenant-master/
├── infra/                      # Infraestructura como código
│   ├── core/                   # Stack principal
│   ├── deployments/            # Plantillas para dedicados
│   └── scripts/                # Scripts de operaciones
├── app/                        # Aplicación
│   ├── backend/                # Django + API
│   └── products/               # Productos (placeholders)
└── specs/                      # Documentación
```

## 🔧 Operaciones

### Crear Tenant Shared

Desde el panel → Crear Workspace → tipo "Shared"

Automáticamente:
- Crea DB en PostgreSQL
- Ejecuta migraciones
- Genera subdominio: `{nombre}.surgir.online`

### Crear Tenant Dedicado

1. Desde el panel → Crear Workspace → tipo "Dedicated"
2. Sistema crea configuración y stack en Portainer
3. Stack dedicado levanta en su propio namespace

### Migraciones

Aplicar migraciones a todos los tenants:
```bash
docker exec tenant-master-panel python /scripts/migrate_all.py
```

### Backups

Ejecutar backup de todas las bases de datos:
```bash
docker exec tenant-master-panel bash /scripts/backup.sh
```

## 🌐 Productos Disponibles

- 📦 Sistema de Inventario
- 💼 Sistema ERP
- 🛒 E-commerce
- 🌐 Landing Pages

## 🔒 Seguridad

- TLS automático con Let's Encrypt
- Cookies seguras (HttpOnly, Secure, SameSite)
- Aislamiento de datos por tenant
- Secrets vía variables de entorno
- Solo superusuario accede al panel

## 📊 Monitoreo

- Logs: `docker logs -f tenant-master-panel`
- Health checks automáticos
- Portainer dashboard para métricas

## 🆘 Troubleshooting

### Panel no accesible

1. Verificar DNS: `nslookup panel.surgir.online`
2. Verificar contenedores: `docker ps`
3. Ver logs: `docker logs tenant-master-traefik`

### Tenant no accesible

1. Verificar en panel que el workspace está activo
2. Verificar DB existe: `docker exec tenant-master-postgres psql -U tenant_admin -l`
3. Ver logs: `docker logs tenant-master-panel`

## 📝 Licencia

Privado - Uso interno

## 👥 Contacto

jesus@surgir.online
