from django.db import models


class Persona(models.Model):
    class TipoPersona(models.TextChoices):
        PERSONA = "PERSONA", "Persona Física"
        EMPRESA = "EMPRESA", "Empresa"

    class Rol(models.TextChoices):
        DUENO = "DUENO", "Dueño / Locador"
        ARRENDATARIO = "ARRENDATARIO", "Arrendatario / Locatario"
        CONTRATISTA = "CONTRATISTA", "Contratista"
        CHOFER = "CHOFER", "Chofer"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        RESPONSABLE_CARGA = "RESPONSABLE_CARGA", "Responsable de Carga"
        BENEFICIARIO = "BENEFICIARIO", "Beneficiario de Pagos"
        PRODUCTOR = "PRODUCTOR", "Productor"

    nombre = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TipoPersona.choices, default=TipoPersona.PERSONA)
    rol = models.CharField(max_length=30, choices=Rol.choices, blank=True, null=True)
    documento = models.CharField(max_length=50, blank=True, null=True)
    cuil = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_rol_display()})" if self.rol else self.nombre


class Campo(models.Model):
    class EstadoContrato(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        VENCIDO = "VENCIDO", "Vencido"
        PENDIENTE = "PENDIENTE", "Pendiente"
        RENOVADO = "RENOVADO", "Renovado"

    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    localidad = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100, blank=True, null=True)
    productor = models.ForeignKey(
        Persona, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='campos_productor'
    )
    superficie_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    superficie_trabajada = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    contrato_asociado = models.ForeignKey('Documento', on_delete=models.SET_NULL, null=True, blank=True, related_name='campos_contrato')
    locatarios = models.ManyToManyField(Persona, blank=True, related_name='campos_arrendatario')
    locadores = models.ManyToManyField(Persona, blank=True, related_name='campos_dueño')
    condiciones_alquiler = models.TextField(blank=True, null=True)
    estado_contrato = models.CharField(max_length=20, choices=EstadoContrato.choices, default=EstadoContrato.ACTIVO)
    observaciones = models.TextField(blank=True, null=True)
    costo_total = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    costo_por_ha = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    margen = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    alquiler_pendiente = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campo"
        verbose_name_plural = "Campos"

    def __str__(self):
        return self.nombre


class Campana(models.Model):
    nombre = models.CharField(max_length=50)
    inicio = models.DateField()
    fin = models.DateField(blank=True, null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Campaña"
        verbose_name_plural = "Campañas"
        ordering = ['-inicio']

    def __str__(self):
        return self.nombre


class Cultivo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    abreviatura = models.CharField(max_length=10, blank=True, null=True)
    familia = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cultivo"
        verbose_name_plural = "Cultivos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Insumo(models.Model):
    class TipoInsumo(models.TextChoices):
        HERBICIDA = "HERBICIDA", "Herbicida"
        FERTILIZANTE = "FERTILIZANTE", "Fertilizante"
        FUNGICIDA = "FUNGICIDA", "Fungicida"
        INSECTICIDA = "INSECTICIDA", "Insecticida"
        SEMILLA = "SEMILLA", "Semilla"
        COADYUVANTE = "COADYUVANTE", "Coadyuvante / Aceite"
        INOCULANTE = "INOCULANTE", "Inoculante"
        SERVICIO = "SERVICIO", "Servicio"
        OTRO = "OTRO", "Otro"

    nombre = models.CharField(max_length=200, unique=True)
    tipo = models.CharField(max_length=20, choices=TipoInsumo.choices)
    unidad = models.CharField(max_length=20)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class ProductoPrecio(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='precios')
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.CharField(max_length=10, default="USD")
    proveedor = models.ForeignKey(
        Persona, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='productos_proveedor'
    )
    fecha_precio = models.DateField()
    vigencia_desde = models.DateField(blank=True, null=True)
    vigencia_hasta = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Precio de Producto"
        verbose_name_plural = "Precios de Productos"
        ordering = ['-fecha_precio']

    def __str__(self):
        return f"{self.insumo.nombre} - {self.precio_unitario} {self.moneda} ({self.fecha_precio})"


class Lote(models.Model):
    campo = models.ForeignKey(Campo, on_delete=models.CASCADE, related_name='lotes')
    campana = models.ForeignKey(Campana, on_delete=models.CASCADE, related_name='lotes')
    nombre = models.CharField(max_length=100)
    cultivo = models.ForeignKey(Cultivo, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes')
    superficie = models.DecimalField(max_digits=10, decimal_places=2)
    rendimiento_estimado = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    precio_tn = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    tipo_cambio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    ubicacion = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        unique_together = ('campo', 'campana', 'nombre')
        ordering = ['-campana__inicio', 'campo__nombre']

    def __str__(self):
        return f"{self.campo.nombre} - {self.campana.nombre} - {self.cultivo.nombre if self.cultivo else self.nombre}"


class TipoLaborPersonalizado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tipo de labor personalizado"
        verbose_name_plural = "Tipos de labor personalizados"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Labor(models.Model):
    class TipoLabor(models.TextChoices):
        SIEMBRA = "SIEMBRA", "Siembra"
        PULVERIZACION_TERRESTRE = "PULVERIZACION_TERRESTRE", "Pulverización terrestre"
        PULVERIZACION_DRONES = "PULVERIZACION_DRONES", "Pulverización con drones"
        PULVERIZACION_AEREA = "PULVERIZACION_AEREA", "Pulverización aérea"
        FERTILIZACION_TERRESTRE = "FERTILIZACION_TERRESTRE", "Fertilización terrestre"
        FERTILIZACION_DRONES = "FERTILIZACION_DRONES", "Fertilización con drones"
        COSECHA = "COSECHA", "Cosecha"
        OTRA = "OTRA", "Otra"

    class EstadoLabor(models.TextChoices):
        CARGADA = "CARGADA", "Cargada"
        PENDIENTE_REVISION = "PENDIENTE_REVISION", "Pendiente de revisión"
        REVISADA = "REVISADA", "Revisada"
        APROBADA = "APROBADA", "Aprobada"
        PENDIENTE_FACTURA = "PENDIENTE_FACTURA", "Pendiente de facturar"
        FACTURADA = "FACTURADA", "Facturada"
        COBRADA = "COBRADA", "Cobrada"

    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='labores')
    tipo = models.CharField(max_length=30, choices=TipoLabor.choices)
    sub_tipo_otra = models.ForeignKey(
        TipoLaborPersonalizado, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='labores'
    )
    estado = models.CharField(
        max_length=30, choices=EstadoLabor.choices, default=EstadoLabor.CARGADA
    )
    fecha = models.DateField()
    hectareas = models.DecimalField(max_digits=10, decimal_places=2)
    precio_por_ha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    moneda = models.CharField(max_length=10, blank=True, null=True, default="USD")
    contratista = models.ForeignKey(
        Persona, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labores_realizadas'
    )
    responsable = models.ForeignKey(
        Persona, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labores_responsable'
    )
    foto_receta = models.ImageField(upload_to='recetas/', blank=True, null=True)
    costo_total = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    costo_dolares_ha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_pesos_ha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    qq_ha = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    cargada_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labores_cargadas'
    )
    fecha_hora_carga = models.DateTimeField(blank=True, null=True)
    revisada_por = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labores_revisadas'
    )
    fecha_revision = models.DateTimeField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Labor"
        verbose_name_plural = "Labores"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.lote.campo.nombre} - {self.fecha}"

    def save(self, *args, **kwargs):
        if self.precio_por_ha and self.hectareas:
            self.costo_total = self.precio_por_ha * self.hectareas
        if self.pk is None:
            if not self.estado:
                self.estado = self.EstadoLabor.CARGADA
            if not self.fecha_hora_carga:
                from django.utils import timezone
                self.fecha_hora_carga = timezone.now()
        super().save(*args, **kwargs)


class LaborInsumo(models.Model):
    labor = models.ForeignKey(Labor, on_delete=models.CASCADE, related_name='insumos')
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='labores')
    precio_referencia = models.ForeignKey(
        ProductoPrecio, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labores_insumo'
    )
    total_aplicado = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    dosis = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    dosis_calculada = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    unidad_dosis = models.CharField(max_length=20, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_total = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)

    class Meta:
        unique_together = ('labor', 'insumo')

    def __str__(self):
        return f"{self.labor} - {self.insumo.nombre}"

    def save(self, *args, **kwargs):
        if self.total_aplicado and self.labor and self.labor.hectareas:
            self.dosis_calculada = self.total_aplicado / self.labor.hectareas
        if self.total_aplicado and self.precio_unitario:
            self.costo_total = self.total_aplicado * self.precio_unitario
        super().save(*args, **kwargs)


class Flete(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        EN_TRASLADO = "EN_TRASLADO", "En Traslado"
        ENTREGADO = "ENTREGADO", "Entregado"
        FACTURADO = "FACTURADO", "Facturado"

    nro_cpe = models.CharField(max_length=50, unique=True, verbose_name="Número de CPE")
    ctg = models.CharField(max_length=50, blank=True, null=True, verbose_name="CTG")
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='fletes', null=True, blank=True)
    patente_camion = models.CharField(max_length=10, verbose_name="Patente Camión")
    patente_acoplado = models.CharField(max_length=10, blank=True, null=True, verbose_name="Patente Acoplado")
    chofer = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True, related_name='fletes_chofer')
    fecha_hora_salida = models.DateTimeField(blank=True, null=True)
    fecha_hora_llegada = models.DateTimeField(blank=True, null=True)
    peso_origen = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    peso_destino = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    flete_corto = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    flete_largo = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    comision = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    secada = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cosecha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    costo_comercial = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    destino = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Flete"
        verbose_name_plural = "Fletes"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Flete {self.nro_cpe} - {self.chofer}" if self.chofer else f"Flete {self.nro_cpe}"


class Documento(models.Model):
    class TipoDocumento(models.TextChoices):
        CONTRATO = "CONTRATO", "Contrato"
        FACTURA = "FACTURA", "Factura"
        COMPROBANTE = "COMPROBANTE", "Comprobante de Pago"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        MAPA = "MAPA", "Mapa"
        OTRO = "OTRO", "Otro"

    class EstadoDocumento(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de Revisar"
        APROBADO = "APROBADO", "Aprobado"
        VENCIDO = "VENCIDO", "Vencido"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    tipo = models.CharField(max_length=20, choices=TipoDocumento.choices)
    numero = models.CharField(max_length=100)
    campo = models.ForeignKey(Campo, on_delete=models.CASCADE, null=True, blank=True, related_name='documentos')
    labor = models.ForeignKey(Labor, on_delete=models.CASCADE, null=True, blank=True, related_name='documentos')
    flete = models.ForeignKey(Flete, on_delete=models.CASCADE, null=True, blank=True, related_name='documentos')
    titular = models.ForeignKey(Persona, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos')
    archivo = models.FileField(upload_to='documentos/', blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=EstadoDocumento.choices, default=EstadoDocumento.PENDIENTE)
    fecha_documento = models.DateField(blank=True, null=True)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    monto = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['-fecha_creacion']
        unique_together = ('tipo', 'numero')

    def __str__(self):
        return f"{self.get_tipo_display()} {self.numero}"


class Parametro(models.Model):
    class Categoria(models.TextChoices):
        GRANO = "GRANO", "Granos"
        INSUMO = "INSUMO", "Insumos"
        LABOR = "LABOR", "Labores"
        COMERCIALIZACION = "COMERCIALIZACION", "Comercialización"
        COSECHA = "COSECHA", "Cosecha"
        TIPO_CAMBIO = "TIPO_CAMBIO", "Tipo de Cambio"
        UNIDAD = "UNIDAD", "Unidades"

    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=30, choices=Categoria.choices)
    valor = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)
    unidad = models.CharField(max_length=20, blank=True, null=True)
    campana = models.ForeignKey(Campana, on_delete=models.SET_NULL, null=True, blank=True, related_name='parametros')
    vigente = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_vigencia_desde = models.DateField(blank=True, null=True)
    fecha_vigencia_hasta = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parámetro"
        verbose_name_plural = "Parámetros"
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"
