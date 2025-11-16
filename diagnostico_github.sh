#!/bin/bash
# Script para verificar y diagnosticar el problema del repositorio

echo "=== DIAGNÓSTICO DE REPOSITORIO GITHUB ==="
echo ""

# 1. Verificar que el contenedor está corriendo
echo "1. Verificando contenedor..."
docker ps | grep tenant-master-panel
echo ""

# 2. Verificar token dentro del contenedor
echo "2. Verificando token GitHub..."
docker exec tenant-master-panel bash -c "cat /app/.env | grep GITHUB_TOKEN"
echo ""

# 3. Probar el script de verificación
echo "3. Probando conexión a GitHub..."
docker exec tenant-master-panel python3 /app/infra/scripts/test_github_config.py
echo ""

# 4. Ver logs recientes del panel
echo "4. Logs recientes del panel (últimas 50 líneas):"
docker logs tenant-master-panel --tail 50
echo ""

# 5. Verificar si existe la carpeta del proyecto
echo "5. Verificando carpeta /opt/proyectos/erp-system:"
docker exec tenant-master-panel ls -la /opt/proyectos/ 2>/dev/null || echo "No existe /opt/proyectos/"
echo ""

# 6. Ver el resultado del último intento de crear repo
echo "6. Intentando crear repo de prueba manualmente..."
docker exec tenant-master-panel python3 /app/infra/scripts/initialize_product_repo.py erp
echo ""

echo "=== FIN DEL DIAGNÓSTICO ==="
