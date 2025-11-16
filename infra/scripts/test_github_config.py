#!/usr/bin/env python3
"""
Script para verificar configuración de GitHub
"""

import os
import sys

def check_github_config():
    """Verifica que el GitHub token esté configurado"""
    print("=== VERIFICANDO CONFIGURACIÓN GITHUB ===\n")
    
    # 1. Verificar variables de entorno
    token = os.getenv('GITHUB_TOKEN')
    username = os.getenv('GITHUB_USERNAME')
    
    if not token:
        print("❌ GITHUB_TOKEN no configurado")
        print("   Ejecuta: export GITHUB_TOKEN=tu_token")
        return False
    
    if not username:
        print("⚠️ GITHUB_USERNAME no configurado, usando 'kritaar' por defecto")
        username = 'kritaar'
    
    print(f"✅ GITHUB_TOKEN configurado (longitud: {len(token)} caracteres)")
    print(f"✅ GITHUB_USERNAME: {username}")
    
    # 2. Verificar que el token funcione
    print("\n=== PROBANDO CONEXIÓN A GITHUB ===\n")
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token válido - Usuario: {user_data.get('login')}")
            print(f"   Nombre: {user_data.get('name', 'N/A')}")
            print(f"   Repos públicos: {user_data.get('public_repos', 0)}")
            print(f"   Repos privados: {user_data.get('total_private_repos', 0)}")
            return True
        else:
            print(f"❌ Token inválido - Status: {response.status_code}")
            print(f"   Error: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a GitHub: {e}")
        return False

if __name__ == '__main__':
    success = check_github_config()
    sys.exit(0 if success else 1)
