from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# ============================================
# PRODUCTOS E INVENTARIO
# ============================================

class Producto(models.Model):
    TIPO_CONTROL_CHOICES = [
        ('NINGUNO', 'Sin Control'),
        ('LOTE', 'Por Lote'),
        ('SERIE', 'Por Serie'),
        ('LOTE_SERIE', 'Lote + Serie'),
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=255)
    categoria = models.CharField(max_length=100)
    marca = models.CharField(max_length=100)
    tipo_control = models.CharField(
        max_length=20,
        choices=TIPO_CONTROL_CHOICES,
        default='NINGUNO'
    )
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    precio_compra_promedio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ubicacion = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    @property
    def requiere_reabastecimiento(self):
        return self.stock_actual <= self.stock_minimo


class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=100)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    cantidad_actual = models.IntegerField(default=0)
    cantidad_inicial = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fecha_vencimiento']
        unique_together = ['producto', 'numero_lote']
    
    def __str__(self):
        return f"{self.producto.codigo} - Lote {self.numero_lote}"


class Serie(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='series')
    numero_serie = models.CharField(max_length=100, unique=True)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('DISPONIBLE', 'Disponible'),
            ('VENDIDO', 'Vendido'),
            ('GARANTIA', 'En Garantía'),
        ],
        default='DISPONIBLE'
    )
    fecha_venta = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.producto.codigo} - S/N {self.numero_serie}"


# ============================================
# CLIENTES
# ============================================

class Cliente(models.Model):
    TIPO_DOCUMENTO_CHOICES = [
        ('DNI', 'DNI'),
        ('RUC', 'RUC'),
        ('CE', 'Carné de Extranjería'),
        ('PASAPORTE', 'Pasaporte'),
    ]
    
    TIPO_CLIENTE_CHOICES = [
        ('PARTICULAR', 'Particular'),
        ('EMPRESA', 'Empresa'),
        ('MECÁNICO', 'Mecánico'),
    ]
    
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES)
    numero_documento = models.CharField(max_length=20, unique=True)
    nombre_completo = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES)
    total_comprado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_comprado']
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.numero_documento} - {self.nombre_completo}"


# ============================================
# PROVEEDORES
# ============================================

class Proveedor(models.Model):
    ruc = models.CharField(max_length=11, unique=True)
    razon_social = models.CharField(max_length=255)
    nombre_comercial = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    total_comprado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_comprado']
        verbose_name_plural = 'Proveedores'
    
    def __str__(self):
        return f"{self.ruc} - {self.razon_social}"


class CatalogoProveedor(models.Model):
    """Productos que ofrece cada proveedor"""
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='catalogo')
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    marca = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    precio_referencial = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['proveedor', 'codigo']
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.proveedor.nombre_comercial} - {self.nombre}"


# ============================================
# COMPRAS
# ============================================

class Compra(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('RECIBIDA', 'Recibida'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    numero_compra = models.CharField(max_length=50, unique=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    fecha_compra = models.DateTimeField()
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    igv = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_compra']
        verbose_name_plural = 'Compras'
    
    def __str__(self):
        return f"Compra {self.numero_compra} - {self.proveedor.razon_social}"


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"


# ============================================
# VENTAS
# ============================================

class Venta(models.Model):
    TIPO_COMPROBANTE_CHOICES = [
        ('BOLETA', 'Boleta'),
        ('FACTURA', 'Factura'),
        ('TICKET', 'Ticket'),
    ]
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('ANULADA', 'Anulada'),
    ]
    
    numero_venta = models.CharField(max_length=50, unique=True)
    tipo_comprobante = models.CharField(max_length=20, choices=TIPO_COMPROBANTE_CHOICES)
    serie_comprobante = models.CharField(max_length=10)
    numero_comprobante = models.CharField(max_length=20)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    fecha_venta = models.DateTimeField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    igv = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_venta']
        verbose_name_plural = 'Ventas'
    
    def __str__(self):
        return f"Venta {self.numero_venta} - {self.cliente.nombre_completo}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    serie = models.ForeignKey(Serie, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"


# ============================================
# MOVIMIENTOS DE INVENTARIO
# ============================================

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('AJUSTE', 'Ajuste'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=255)
    compra = models.ForeignKey(Compra, on_delete=models.SET_NULL, null=True, blank=True)
    venta = models.ForeignKey(Venta, on_delete=models.SET_NULL, null=True, blank=True)
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True)
    serie = models.ForeignKey(Serie, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Movimientos de Inventario'
    
    def __str__(self):
        return f"{self.tipo_movimiento} - {self.producto.codigo} - {self.cantidad}"
