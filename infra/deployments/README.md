# Deployments - Dedicated Tenants

Esta carpeta contiene plantillas para crear deployments dedicados de tenants.

## TEMPLATE

La carpeta `TEMPLATE/` es una plantilla base para crear stacks dedicados. 

### Uso

1. **Crear tenant dedicado desde el panel**
2. **El sistema automáticamente:**
   - Duplica TEMPLATE a una nueva carpeta
   - Configura variables de entorno
   - Crea stack en Portainer desde Git

### Estructura

```
TEMPLATE/
├── docker-compose.yml    # Stack completo (app + postgres + redis)
├── .env.example          # Variables de entorno
└── postgres/             # Datos de PostgreSQL
    └── .gitkeep
```

## Variables Requeridas

- `TENANT_NAME`: Nombre único del tenant
- `TENANT_DOMAIN`: Subdominio completo (ej: acme.surgir.online)
- `TENANT_DB_NAME`: Nombre de la base de datos
- `TENANT_DB_USER`: Usuario de PostgreSQL
- `TENANT_DB_PASSWORD`: Contraseña segura

## Notas

- Cada tenant dedicado tiene su propio Postgres aislado
- Comparten la red `tenant-network` con el core para Traefik
- Redis puede ser compartido o dedicado según necesidad
