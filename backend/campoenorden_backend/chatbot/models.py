from django.db import models


class Maquinaria(models.Model):
    TIPO_CHOICES = [
        ('TRACTOR', 'Tractor'),
        ('COSECHADORA', 'Cosechadora'),
        ('PULVERIZADORA', 'Pulverizadora'),
        ('SEMBRADORA', 'Sembradora'),
        ('CAMION', 'Camión'),
        ('CAMIONETA', 'Camioneta'),
        ('DRONE', 'Drone'),
        ('AVION', 'Avión fumigador'),
        ('OTRO', 'Otro'),
    ]
    PROPIETARIO_CHOICES = [
        ('PROPIA', 'Propia'),
        ('CONTRATISTA', 'Contratista'),
    ]

    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OTRO')
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    ano = models.IntegerField(null=True, blank=True)
    dominio = models.CharField(max_length=20, blank=True)
    hp = models.IntegerField(null=True, blank=True)
    propietario = models.CharField(max_length=20, choices=PROPIETARIO_CHOICES, default='PROPIA')
    precio_mercado_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vencimiento_seguro = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maquinaria'
        verbose_name_plural = 'Maquinaria'
        ordering = ['tipo', 'nombre']

    def __str__(self):
        return self.nombre


class WhatsAppSession(models.Model):
    phone_number = models.CharField(max_length=30, unique=True, db_index=True)
    user = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='whatsapp_sessions',
    )
    current_flow = models.CharField(max_length=50, blank=True, default='')
    current_step = models.IntegerField(default=0)
    session_data = models.JSONField(default=dict)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sesión WhatsApp'
        verbose_name_plural = 'Sesiones WhatsApp'

    def __str__(self):
        user_str = self.user.username if self.user else 'sin usuario'
        return f"{self.phone_number} ({user_str}) — {self.current_flow or 'menu'}"


class WhatsAppMessage(models.Model):
    DIRECTION_IN = 'IN'
    DIRECTION_OUT = 'OUT'
    DIRECTION_CHOICES = [
        (DIRECTION_IN, 'Entrante'),
        (DIRECTION_OUT, 'Saliente'),
    ]

    session = models.ForeignKey(
        WhatsAppSession, on_delete=models.CASCADE, related_name='messages',
    )
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, default='text')
    content = models.TextField(blank=True)
    media_id = models.CharField(max_length=200, blank=True)
    whatsapp_message_id = models.CharField(max_length=200, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Mensaje WhatsApp'
        verbose_name_plural = 'Mensajes WhatsApp'

    def __str__(self):
        return f"{self.direction} {self.message_type} — {self.timestamp:%Y-%m-%d %H:%M}"


class RegistroCombustible(models.Model):
    maquinaria = models.ForeignKey(
        Maquinaria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='combustibles',
    )
    campo = models.ForeignKey(
        'core.Campo', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='combustibles',
    )
    fecha = models.DateField()
    proveedor = models.CharField(max_length=200, blank=True)
    cuit_proveedor = models.CharField(max_length=20, blank=True)
    litros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_litro = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nro_documento = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    cargado_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='combustibles_cargados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Combustible'
        verbose_name_plural = 'Registros de Combustible'

    def __str__(self):
        m = str(self.maquinaria) if self.maquinaria else '-'
        return f"Combustible {self.fecha} — {m}"


class RegistroMantenimiento(models.Model):
    TIPO_CHOICES = [
        ('SERVICE', 'Service'),
        ('REP_MECANICA', 'Reparación mecánica'),
        ('ELECTRICA', 'Eléctrica'),
        ('NEUMATICOS', 'Neumáticos'),
        ('CHAPA_PINTURA', 'Chapa y pintura'),
        ('OTRO', 'Otro'),
    ]
    QUIEN_CHOICES = [
        ('PERSONAL_PROPIO', 'Personal propio'),
        ('TALLER', 'Taller mecánico'),
        ('CONCESIONARIO', 'Concesionario oficial'),
    ]
    PAGO_CHOICES = [
        ('CHEQUE', 'Cheque'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('EFECTIVO', 'Efectivo'),
    ]

    maquinaria = models.ForeignKey(
        Maquinaria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mantenimientos',
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    fecha = models.DateField()
    descripcion = models.TextField(blank=True)
    repuesto = models.CharField(max_length=500, blank=True)
    quien_realizo = models.CharField(max_length=20, choices=QUIEN_CHOICES, blank=True)
    taller = models.CharField(max_length=200, blank=True)
    cuit_taller = models.CharField(max_length=20, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nro_factura = models.CharField(max_length=100, blank=True)
    pago_realizado = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=20, choices=PAGO_CHOICES, blank=True)
    observaciones = models.TextField(blank=True)
    cargado_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mantenimientos_cargados',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Mantenimiento'
        verbose_name_plural = 'Registros de Mantenimiento'

    def __str__(self):
        m = str(self.maquinaria) if self.maquinaria else '-'
        return f"Mantenimiento {self.tipo} {self.fecha} — {m}"
