#!/usr/bin/env python
"""
Script para registrar el producto Sistema ERP en la base de datos
Se ejecuta una vez para configurar el producto

Uso:
    python register_erp_product.py
"""

import os
import sys

# Agregar el path del proyecto
sys.path.append('/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from panel.models import Product, Deployment


def register_erp_product():
    """Registra el producto Sistema ERP"""
    
    print("🚀 Registrando producto Sistema ERP...")
    
    # Crear o actualizar producto
    product, created = Product.objects.update_or_create(
        name='erp',
        defaults={
            'display_name': 'Sistema ERP',
            'description': 'Sistema completo de gestión empresarial con inventario, compras, ventas, clientes y proveedores',
            'icon': '📊',
            'template_path': 'TEMPLATE_ERP',
            'backend_image': 'ghcr.io/tenant-master/erp-backend:latest',
            'frontend_image': 'ghcr.io/tenant-master/erp-frontend:latest',
            'requires_database': True,
            'supports_shared': True,
            'supports_dedicated': True,
            'is_active': True,
        }
    )
    
    if created:
        print(f"✅ Producto '{product.display_name}' creado exitosamente")
    else:
        print(f"✅ Producto '{product.display_name}' actualizado")
    
    print(f"\n📋 Detalles del producto:")
    print(f"  - ID: {product.id}")
    print(f"  - Nombre: {product.display_name}")
    print(f"  - Template: {product.template_path}")
    print(f"  - Soporta compartido: {'Sí' if product.supports_shared else 'No'}")
    print(f"  - Soporta dedicado: {'Sí' if product.supports_dedicated else 'No'}")
    
    # Opcional: Crear un deployment compartido inicial
    create_shared = input("\n¿Deseas crear un deployment compartido para este producto? (s/n): ")
    
    if create_shared.lower() == 's':
        deployment, created = Deployment.objects.get_or_create(
            name=f'{product.name}-shared',
            defaults={
                'product': product,
                'deployment_type': 'SHARED',
                'status': 'DEPLOYING',
                'physical_path': f'/var/deployments/{product.name}-shared',
                'docker_compose_content': '',
                'max_tenants': 50,  # Máximo de tenants en el deployment compartido
                'current_tenants': 0,
            }
        )
        
        if created:
            print(f"✅ Deployment compartido '{deployment.name}' creado")
            print(f"   Debes desplegarlo manualmente en el servidor")
        else:
            print(f"ℹ️  Deployment compartido '{deployment.name}' ya existe")
    
    print("\n🎉 ¡Registro completado!")
    print("\nPróximos pasos:")
    print("1. Construir las imágenes Docker del ERP:")
    print("   cd app/products/erp")
    print("   docker build -t ghcr.io/tenant-master/erp-backend:latest ./backend")
    print("   docker build -t ghcr.io/tenant-master/erp-frontend:latest ./frontend")
    print("\n2. Subir las imágenes al registry:")
    print("   docker push ghcr.io/tenant-master/erp-backend:latest")
    print("   docker push ghcr.io/tenant-master/erp-frontend:latest")
    print("\n3. Crear un workspace desde el panel con el producto 'Sistema ERP'")


if __name__ == '__main__':
    register_erp_product()
