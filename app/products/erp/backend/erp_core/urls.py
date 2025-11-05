from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'productos', views.ProductoViewSet)
router.register(r'lotes', views.LoteViewSet)
router.register(r'series', views.SerieViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'proveedores', views.ProveedorViewSet)
router.register(r'catalogo-proveedores', views.CatalogoProveedorViewSet)
router.register(r'compras', views.CompraViewSet)
router.register(r'ventas', views.VentaViewSet)
router.register(r'movimientos', views.MovimientoInventarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
