#!/usr/bin/env python3
import sys
import json
import subprocess
import os

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
    
    project_path = f"/opt/proyectos/{product_name}-system"
    compose_file = f"{project_path}/docker-compose.yml"
    url = f"https://{subdomain}.surgir.online"
    
    try:
        if not os.path.exists(project_path):
            print(f"ERROR: El directorio {project_path} no existe")
            result = {
                'success': False,
                'error': f'Directorio {project_path} no encontrado'
            }
        else:
            if not os.path.exists(compose_file):
                print(f"ERROR: docker-compose.yml no existe en {project_path}")
                result = {
                    'success': False,
                    'error': 'docker-compose.yml no encontrado'
                }
            else:
                print(f"✓ Proyecto compartido encontrado en {project_path}")
                result = {
                    'success': True,
                    'url': url,
                    'project_path': project_path
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
