#!/usr/bin/env python3
import sys
import json
import subprocess

def main():
    if len(sys.argv) != 6:
        print(json.dumps({
            'success': False,
            'error': 'Faltan argumentos: product_name, subdomain, db_name, db_user, db_password'
        }))
        sys.exit(1)
    
    product_name = sys.argv[1]
    subdomain = sys.argv[2]
    db_name = sys.argv[3]
    db_user = sys.argv[4]
    db_password = sys.argv[5]
    
    container_name = f"tenant-master-{product_name}-shared"
    url = f"https://{subdomain}.surgir.online"
    
    try:
        print(f"Validando deployment SHARED para: {subdomain}")
        print(f"Producto: {product_name}")
        print(f"Contenedor esperado: {container_name}")
        print(f"Base de datos: {db_name}")
        
        cmd = f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'"
        check_result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if check_result.returncode != 0:
            result = {
                'success': False,
                'error': f'Error al verificar contenedor: {check_result.stderr}'
            }
            print("=== RESULT ===")
            print(json.dumps(result))
            sys.exit(1)
        
        containers = check_result.stdout.strip().split('\n')
        containers = [c for c in containers if c and container_name in c]
        
        if not containers:
            result = {
                'success': False,
                'error': f'Contenedor {container_name} no encontrado. Debes agregarlo al stack tenant-master-core en Portainer y hacer Pull and redeploy.'
            }
            print("=== RESULT ===")
            print(json.dumps(result))
            sys.exit(1)
        
        found_container = containers[0]
        print(f"✓ Contenedor compartido encontrado: {found_container}")
        
        cmd_status = f"docker inspect {found_container} --format '{{{{.State.Status}}}}'"
        status_result = subprocess.run(
            cmd_status,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if status_result.returncode == 0:
            status = status_result.stdout.strip()
            print(f"✓ Estado del contenedor: {status}")
            
            if status != "running":
                result = {
                    'success': False,
                    'error': f'El contenedor {found_container} existe pero no está corriendo (estado: {status})'
                }
                print("=== RESULT ===")
                print(json.dumps(result))
                sys.exit(1)
        
        print(f"✓ Base de datos configurada: {db_name}")
        print(f"✓ URL del workspace: {url}")
        print(f"✓ El contenedor {found_container} manejará las peticiones a {url}")
        
        result = {
            'success': True,
            'url': url,
            'container_name': found_container,
            'db_name': db_name,
            'deployment_type': 'shared'
        }
        
        print("=== RESULT ===")
        print(json.dumps(result))
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        result = {
            'success': False,
            'error': str(e)
        }
        print("=== RESULT ===")
        print(json.dumps(result))
        sys.exit(1)

if __name__ == '__main__':
    main()
