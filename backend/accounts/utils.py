"""
Utilidades para gestión de tenants
"""
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


def create_tenant_database(product_name, subdomain, company_name):
    """
    Crea una nueva base de datos para el tenant usando el script en el VPS
    
    Args:
        product_name: Nombre del producto (inventario, erp, shop)
        subdomain: Subdominio del tenant (empresaa, empresab)
        company_name: Nombre de la empresa
    
    Returns:
        dict: Credenciales de la BD creada
    """
    try:
        # Ejecutar script de creación en el VPS
        result = subprocess.run(
            ['/opt/databases/postgresql/create_tenant.sh', product_name, subdomain, company_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # El script devuelve las credenciales
        # Formato esperado: DB: nombre | User: usuario | Pass: contraseña
        output = result.stdout.strip()
        
        # Parsear la salida (esto es una implementación básica)
        # En producción, el script debería devolver JSON
        lines = output.split('\n')
        credentials = {}
        
        for line in lines:
            if 'DB:' in line:
                credentials['db_name'] = line.split('DB:')[1].split('|')[0].strip()
            if 'User:' in line:
                credentials['db_user'] = line.split('User:')[1].split('|')[0].strip()
            if 'Pass:' in line:
                credentials['db_password'] = line.split('Pass:')[1].strip()
        
        logger.info(f"Base de datos creada exitosamente para: {subdomain}")
        return credentials
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al crear BD: {e.stderr}")
        raise Exception(f"No se pudo crear la base de datos: {e.stderr}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise Exception(f"Error al procesar la creación de la base de datos: {str(e)}")


def apply_tenant_migrations(workspace):
    """
    Aplica las migraciones de Django a la nueva BD del tenant
    
    Nota: Esta función se ejecutaría idealmente desde el contenedor del producto
    correspondiente (inventario, erp, shop) no desde tenant-master.
    """
    # TODO: Implementar trigger al contenedor del producto
    # Por ahora, las migraciones se aplicarán cuando el tenant acceda por primera vez
    pass
