from django.contrib import admin
from .models import *

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria', 'marca', 'stock_actual', 'stock_minimo', 'precio_venta', 'activo']
    list_filter = ['categoria', 'marca', 'tipo_control', 'activo']
    search_fields = ['codigo', 'nombre', 'marca']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_documento', 'nombre_completo', 'tipo_cliente', 'total_comprado', 'activo']
    list_filter = ['tipo_documento', 'tipo_cliente', 'activo']
    search_fields = ['numero_documento', 'nombre_completo']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['ruc', 'razon_social', 'nombre_comercial', 'total_comprado', 'activo']
    search_fields = ['ruc', 'razon_social', 'nombre_comercial']

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ['numero_compra', 'proveedor', 'fecha_compra', 'total', 'estado']
    list_filter = ['estado', 'fecha_compra']
    search_fields = ['numero_compra']

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['numero_venta', 'cliente', 'fecha_venta', 'total', 'estado']
    list_filter = ['tipo_comprobante', 'estado', 'fecha_venta']
    search_fields = ['numero_venta', 'numero_comprobante']

admin.site.register(Lote)
admin.site.register(Serie)
admin.site.register(CatalogoProveedor)
admin.site.register(MovimientoInventario)
