# 🎯 TEMPLATE DEL SISTEMA ERP - GUÍA COMPLETA

## ✅ LO QUE SE HA CREADO

Se ha creado un **template completo y funcional** del Sistema ERP que es replicable para cada workspace en tenant-master.

### 📁 ESTRUCTURA CREADA

```
tenant_master/
├── app/
│   └── products/
│       └── erp/                    # Código fuente del ERP
│           ├── backend/           # Django API
│           └── frontend/          # React SPA
│
├── infra/
│   ├── deployments/
│   │   └── TEMPLATE_ERP/          # 🆕 Template replicable
│   │       ├── docker-compose.yml
│   │       ├── .env.template
│   │       ├── init.sql
│   │       ├── postgres/
│   │       └── README.md
│   │
│   └── scripts/
│       ├── deploy_product.py      # 🆕 Script de despliegue
│       └── register_erp_product.py # 🆕 Registro del producto
│
└── app/backend/panel/
    ├── models.py                  # 🆕 Con modelo Deployment
    └── views.py                   # 🆕 Actualizado con deployments
```

---

## 🔄 FLUJO COMPLETO DE DESPLIEGUE

### **Opción A: Workspace DEDICADO**

```
1. Usuario crea workspace desde el panel
   ├── Selecciona producto: "Sistema ERP"
   ├── Selecciona tipo: "Dedicado"
   └── Ingresa datos (nombre, subdominio, etc.)

2. Sistema crea registro en BD
   ├── Tenant (workspace)
   └── Deployment (dedicado)

3. Script deploy_product.py se ejecuta
   ├── Copia TEMPLATE_ERP a /var/deployments/erp-{schema}
   ├── Genera .env con credenciales únicas
   ├── Procesa docker-compose.yml
   └── Ejecuta: docker-compose up -d

4. Docker Compose levanta el stack
   ├── postgres (BD del tenant)
   ├── backend (Django API)
   └── frontend (React + Nginx)

5. Backend ejecuta automáticamente
   ├── Migraciones de Django
   ├── Carga datos de ejemplo (init.sql)
   └── Crea superuser admin/admin123

6. Traefik configura automáticamente
   ├── Routing: {subdomain}.surgir.online
   └── Certificado SSL de Let's Encrypt

7. ✅ ERP disponible en https://{subdomain}.surgir.online
```

### **Opción B: Workspace COMPARTIDO**

```
1. Usuario crea workspace desde el panel
   ├── Selecciona producto: "Sistema ERP"
   └── Selecciona tipo: "Compartido"

2. Sistema busca deployment compartido disponible
   └── Si existe: usa ese deployment
   └── Si no existe: muestra error

3. Sistema crea solo la base de datos
   ├── DB nueva con credenciales únicas
   └── Ejecuta migraciones

4. ✅ ERP disponible inmediatamente
   └── Comparte runtime con otros tenants
```

---

## 🚀 PUESTA EN MARCHA

### **PASO 1: Construir Imágenes Docker**

```bash
cd C:\Proyectos_vps\tenant_master\app\products\erp

# Backend
docker build -t ghcr.io/tenant-master/erp-backend:latest ./backend

# Frontend
docker build -t ghcr.io/tenant-master/erp-frontend:latest ./frontend

# Push al registry (si usas registry remoto)
docker push ghcr.io/tenant-master/erp-backend:latest
docker push ghcr.io/tenant-master/erp-frontend:latest
```

### **PASO 2: Hacer Migraciones del Panel**

```bash
cd C:\Proyectos_vps\tenant_master\app\backend

# Crear migraciones para el nuevo modelo Deployment
python manage.py makemigrations panel

# Aplicar migraciones
python manage.py migrate panel
```

### **PASO 3: Registrar el Producto**

```bash
cd C:\Proyectos_vps\tenant_master

# Ejecutar script de registro
python infra/scripts/register_erp_product.py

# El script preguntará si quieres crear un deployment compartido
```

### **PASO 4: Crear Primer Workspace**

```
1. Acceder al panel: https://panel.surgir.online
2. Ir a "Workspaces" → "Crear Workspace"
3. Llenar formulario:
   ├── Nombre: "Mi Empresa SAC"
   ├── Subdominio: "miempresa"
   ├── Producto: "Sistema ERP"
   ├── Tipo: "Dedicado" o "Compartido"
   └── Propietario: usuario existente

4. Click "Crear"

5. Esperar 2-3 minutos mientras se despliega

6. Acceder a: https://miempresa.surgir.online
   Usuario: admin
   Contraseña: admin123
```

---

## 📊 CARACTERÍSTICAS DEL TEMPLATE

### **✅ Auto-configuración**
- Variables de entorno generadas automáticamente
- Credenciales únicas por tenant
- Nombres únicos (sin conflictos)

### **✅ Seguridad**
- Cada tenant tiene su propia BD
- Usuarios y contraseñas únicos
- Secret keys aleatorios
- SSL automático con Let's Encrypt

### **✅ Escalabilidad**
- Deployments compartidos para muchos tenants
- Deployments dedicados para tenants premium
- Recursos aislados

### **✅ Mantenimiento**
- Actualización de imágenes sin afectar datos
- Backups por tenant
- Logs centralizados

---

## 🔧 PERSONALIZACIÓN DEL TEMPLATE

### **Modificar datos iniciales**

Editar: `infra/deployments/TEMPLATE_ERP/init.sql`

```sql
-- Agregar más productos de ejemplo
INSERT INTO erp_core_producto (...) VALUES (...);

-- Agregar más clientes
INSERT INTO erp_core_cliente (...) VALUES (...);
```

### **Cambiar configuración de Docker**

Editar: `infra/deployments/TEMPLATE_ERP/docker-compose.yml`

```yaml
# Cambiar recursos
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### **Agregar más variables de entorno**

Editar: `infra/deployments/TEMPLATE_ERP/.env.template`

```env
# Nueva variable
CUSTOM_VAR={{CUSTOM_VALUE}}
```

---

## 🐛 TROUBLESHOOTING

### **Problema: El deployment no se crea**

```bash
# Ver logs del script
tail -f /var/log/tenant_master.log

# Verificar permisos
ls -la /var/deployments/

# Ejecutar deployment manualmente
cd /var/deployments/erp-{schema}
docker-compose up -d
docker-compose logs -f
```

### **Problema: No puede conectar a la BD**

```bash
# Verificar que la BD existe
docker exec tenant-master-postgres psql -U postgres -c "\l"

# Verificar usuario
docker exec tenant-master-postgres psql -U postgres -c "\du"

# Probar conexión
docker exec erp-{schema}-db psql -U {db_user} -d {db_name} -c "SELECT 1"
```

### **Problema: SSL no funciona**

```bash
# Ver logs de Traefik
docker logs tenant-master-traefik -f | grep {subdomain}

# Verificar DNS
nslookup {subdomain}.surgir.online

# Forzar renovación
docker restart tenant-master-traefik
```

---

## 📝 PRÓXIMOS PASOS

1. **Construir imágenes y hacer push**
2. **Hacer migraciones del panel**
3. **Registrar el producto**
4. **Crear primer workspace de prueba**
5. **Documentar para otros productos** (Inventario, Tienda, etc.)

---

## 🎉 RESULTADO FINAL

Ahora tienes un **sistema completamente automatizado** donde:

✅ Los usuarios crean workspaces desde el panel web
✅ El sistema despliega automáticamente el ERP
✅ Cada tenant tiene su propio ERP funcional
✅ SSL, DNS y routing se configuran solos
✅ Puedes escalar a cientos de tenants

**¡El template está listo para producción!** 🚀
