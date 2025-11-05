from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from .models import *
from .serializers import *


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['codigo', 'nombre', 'marca', 'categoria']
    ordering_fields = ['codigo', 'nombre', 'stock_actual', 'precio_venta']
    filterset_fields = ['categoria', 'marca', 'tipo_control', 'activo']
    
    @action(detail=False, methods=['get'])
    def stock_bajo(self, request):
        """Productos con stock bajo"""
        productos = self.queryset.filter(stock_actual__lte=models.F('stock_minimo'))
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de productos"""
        total = self.queryset.count()
        activos = self.queryset.filter(activo=True).count()
        stock_bajo = self.queryset.filter(stock_actual__lte=models.F('stock_minimo')).count()
        valor_inventario = self.queryset.aggregate(
            total=Sum(models.F('stock_actual') * models.F('precio_compra_promedio'))
        )['total'] or 0
        
        return Response({
            'total_productos': total,
            'productos_activos': activos,
            'productos_stock_bajo': stock_bajo,
            'valor_total_inventario': float(valor_inventario),
        })


class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['numero_lote', 'producto__codigo', 'producto__nombre']
    filterset_fields = ['producto']
    
    @action(detail=False, methods=['get'])
    def proximos_a_vencer(self, request):
        """Lotes próximos a vencer (30 días)"""
        fecha_limite = datetime.now().date() + timedelta(days=30)
        lotes = self.queryset.filter(
            fecha_vencimiento__lte=fecha_limite,
            cantidad_actual__gt=0
        )
        serializer = self.get_serializer(lotes, many=True)
        return Response(serializer.data)


class SerieViewSet(viewsets.ModelViewSet):
    queryset = Serie.objects.all()
    serializer_class = SerieSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['numero_serie', 'producto__codigo', 'producto__nombre']
    filterset_fields = ['producto', 'estado', 'lote']


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['numero_documento', 'nombre_completo', 'telefono', 'email']
    ordering_fields = ['nombre_completo', 'total_comprado', 'created_at']
    filterset_fields = ['tipo_documento', 'tipo_cliente', 'activo']
    
    @action(detail=False, methods=['get'])
    def top_clientes(self, request):
        """Top 10 clientes por compras"""
        clientes = self.queryset.order_by('-total_comprado')[:10]
        serializer = self.get_serializer(clientes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """Historial de compras del cliente"""
        cliente = self.get_object()
        ventas = Venta.objects.filter(cliente=cliente).order_by('-fecha_venta')
        serializer = VentaSerializer(ventas, many=True)
        return Response(serializer.data)


class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['ruc', 'razon_social', 'nombre_comercial']
    ordering_fields = ['razon_social', 'total_comprado']
    filterset_fields = ['activo']
    
    @action(detail=True, methods=['get'])
    def catalogo(self, request, pk=None):
        """Catálogo de productos del proveedor"""
        proveedor = self.get_object()
        catalogo = proveedor.catalogo.filter(activo=True)
        serializer = CatalogoProveedorSerializer(catalogo, many=True)
        return Response(serializer.data)


class CatalogoProveedorViewSet(viewsets.ModelViewSet):
    queryset = CatalogoProveedor.objects.all()
    serializer_class = CatalogoProveedorSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['codigo', 'nombre', 'marca']
    filterset_fields = ['proveedor', 'categoria', 'activo']


class CompraViewSet(viewsets.ModelViewSet):
    queryset = Compra.objects.all()
    serializer_class = CompraSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['numero_compra', 'proveedor__razon_social']
    ordering_fields = ['fecha_compra', 'total']
    filterset_fields = ['proveedor', 'estado']
    
    @action(detail=True, methods=['post'])
    def recibir(self, request, pk=None):
        """Marcar compra como recibida y actualizar inventario"""
        compra = self.get_object()
        
        if compra.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden recibir compras pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar stock y crear movimientos
        for detalle in compra.detalles.all():
            producto = detalle.producto
            producto.stock_actual += detalle.cantidad
            producto.save()
            
            # Crear movimiento
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento='ENTRADA',
                cantidad=detalle.cantidad,
                motivo=f'Compra {compra.numero_compra}',
                compra=compra,
                lote=detalle.lote,
                created_by=request.user
            )
        
        # Actualizar estado
        compra.estado = 'RECIBIDA'
        compra.fecha_recepcion = datetime.now()
        compra.save()
        
        # Actualizar total proveedor
        proveedor = compra.proveedor
        proveedor.total_comprado += compra.total
        proveedor.save()
        
        return Response({'status': 'Compra recibida exitosamente'})


class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['numero_venta', 'numero_comprobante', 'cliente__nombre_completo']
    ordering_fields = ['fecha_venta', 'total']
    filterset_fields = ['cliente', 'tipo_comprobante', 'estado']
    
    @action(detail=True, methods=['post'])
    def confirmar(self, request, pk=None):
        """Confirmar venta y actualizar inventario"""
        venta = self.get_object()
        
        if venta.estado != 'PENDIENTE':
            return Response(
                {'error': 'Solo se pueden confirmar ventas pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar stock y crear movimientos
        for detalle in venta.detalles.all():
            producto = detalle.producto
            producto.stock_actual -= detalle.cantidad
            producto.save()
            
            # Actualizar serie si aplica
            if detalle.serie:
                serie = detalle.serie
                serie.estado = 'VENDIDO'
                serie.fecha_venta = venta.fecha_venta
                serie.save()
            
            # Crear movimiento
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento='SALIDA',
                cantidad=detalle.cantidad,
                motivo=f'Venta {venta.numero_venta}',
                venta=venta,
                lote=detalle.lote,
                serie=detalle.serie,
                created_by=request.user
            )
        
        # Actualizar estado
        venta.estado = 'PAGADA'
        venta.save()
        
        # Actualizar total cliente
        cliente = venta.cliente
        cliente.total_comprado += venta.total
        cliente.save()
        
        return Response({'status': 'Venta confirmada exitosamente'})
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de ventas"""
        hoy = datetime.now().date()
        mes_actual = hoy.replace(day=1)
        
        ventas_hoy = self.queryset.filter(
            fecha_venta__date=hoy,
            estado='PAGADA'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        ventas_mes = self.queryset.filter(
            fecha_venta__date__gte=mes_actual,
            estado='PAGADA'
        ).aggregate(total=Sum('total'))['total'] or 0
        
        return Response({
            'ventas_hoy': float(ventas_hoy),
            'ventas_mes': float(ventas_mes),
        })


class MovimientoInventarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['producto__codigo', 'producto__nombre', 'motivo']
    ordering_fields = ['created_at']
    filterset_fields = ['producto', 'tipo_movimiento']
