# Sistema ERP - Producto Tenant

Sistema ERP completo para gestión de inventario, compras, ventas y más.

## 🎯 Características

- ✅ Gestión de productos con control de inventario (LOTE, SERIE, LOTE+SERIE)
- ✅ Gestión de clientes y proveedores
- ✅ Compras con recepción automática de mercancía
- ✅ Ventas con generación de comprobantes
- ✅ Control de stock y alertas de reabastecimiento
- ✅ Movimientos de inventario trazables
- ✅ Dashboard con estadísticas en tiempo real
- ✅ API REST completa
- ✅ Frontend React responsive

## 🏗️ Arquitectura

- **Backend:** Django + Django REST Framework + PostgreSQL
- **Frontend:** React (CDN) + TailwindCSS
- **Proxy:** Nginx

## 🚀 Deploy

Este proyecto es desplegado automáticamente por `tenant-master` cuando se crea un workspace con el producto "ERP".

### Deploy Manual (para desarrollo)

```bash
# Copiar variables de entorno
cp .env.example .env

# Editar .env con tus valores
nano .env

# Levantar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## 📊 Modelos de Datos

### Productos
- Control de inventario flexible (sin control, por lote, por serie, o ambos)
- Alertas de stock mínimo
- Ubicación en almacén

### Clientes
- Tipos: Particular, Empresa, Mecánico
- Historial de compras
- Documentos: DNI, RUC, CE, Pasaporte

### Proveedores
- Catálogo de productos por proveedor
- Historial de compras

### Compras y Ventas
- Flujo completo con estados
- Actualización automática de inventario
- Trazabilidad completa

## 🔧 API Endpoints

- `GET /api/productos/` - Listar productos
- `POST /api/productos/` - Crear producto
- `GET /api/productos/stock_bajo/` - Productos con stock bajo
- `GET /api/clientes/` - Listar clientes
- `GET /api/proveedores/` - Listar proveedores
- `GET /api/compras/` - Listar compras
- `POST /api/compras/{id}/recibir/` - Recibir mercancía
- `GET /api/ventas/` - Listar ventas
- `POST /api/ventas/{id}/confirmar/` - Confirmar venta
- `GET /api/movimientos/` - Movimientos de inventario

## 👤 Credenciales por Defecto

- **Usuario:** admin
- **Contraseña:** admin123

**⚠️ CAMBIAR EN PRODUCCIÓN**

## 📝 Licencia

Propiedad de Tenant Master System
