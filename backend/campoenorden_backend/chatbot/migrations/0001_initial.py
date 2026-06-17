from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0003_seed_data'),
        ('users', '0003_emailverificationtoken_invitacion_passwordresettoken'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Maquinaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('tipo', models.CharField(
                    choices=[
                        ('TRACTOR', 'Tractor'), ('COSECHADORA', 'Cosechadora'),
                        ('PULVERIZADORA', 'Pulverizadora'), ('SEMBRADORA', 'Sembradora'),
                        ('CAMION', 'Camión'), ('CAMIONETA', 'Camioneta'),
                        ('DRONE', 'Drone'), ('AVION', 'Avión fumigador'), ('OTRO', 'Otro'),
                    ],
                    default='OTRO', max_length=20,
                )),
                ('marca', models.CharField(blank=True, max_length=100)),
                ('modelo', models.CharField(blank=True, max_length=100)),
                ('ano', models.IntegerField(blank=True, null=True)),
                ('dominio', models.CharField(blank=True, max_length=20)),
                ('hp', models.IntegerField(blank=True, null=True)),
                ('propietario', models.CharField(
                    choices=[('PROPIA', 'Propia'), ('CONTRATISTA', 'Contratista')],
                    default='PROPIA', max_length=20,
                )),
                ('precio_mercado_usd', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('vencimiento_seguro', models.DateField(blank=True, null=True)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Maquinaria', 'verbose_name_plural': 'Maquinaria', 'ordering': ['tipo', 'nombre']},
        ),
        migrations.CreateModel(
            name='WhatsAppSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(db_index=True, max_length=30, unique=True)),
                ('current_flow', models.CharField(blank=True, default='', max_length=50)),
                ('current_step', models.IntegerField(default=0)),
                ('session_data', models.JSONField(default=dict)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='whatsapp_sessions',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'Sesión WhatsApp', 'verbose_name_plural': 'Sesiones WhatsApp'},
        ),
        migrations.CreateModel(
            name='WhatsAppMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('direction', models.CharField(
                    choices=[('IN', 'Entrante'), ('OUT', 'Saliente')], max_length=3,
                )),
                ('message_type', models.CharField(default='text', max_length=20)),
                ('content', models.TextField(blank=True)),
                ('media_id', models.CharField(blank=True, max_length=200)),
                ('whatsapp_message_id', models.CharField(blank=True, db_index=True, max_length=200)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='chatbot.whatsappsession',
                )),
            ],
            options={
                'verbose_name': 'Mensaje WhatsApp',
                'verbose_name_plural': 'Mensajes WhatsApp',
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='RegistroCombustible',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('proveedor', models.CharField(blank=True, max_length=200)),
                ('cuit_proveedor', models.CharField(blank=True, max_length=20)),
                ('litros', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('precio_litro', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('nro_documento', models.CharField(blank=True, max_length=100)),
                ('observaciones', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('campo', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='combustibles',
                    to='core.campo',
                )),
                ('cargado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='combustibles_cargados',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('maquinaria', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='combustibles',
                    to='chatbot.maquinaria',
                )),
            ],
            options={
                'verbose_name': 'Registro de Combustible',
                'verbose_name_plural': 'Registros de Combustible',
                'ordering': ['-fecha'],
            },
        ),
        migrations.CreateModel(
            name='RegistroMantenimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(
                    choices=[
                        ('SERVICE', 'Service'), ('REP_MECANICA', 'Reparación mecánica'),
                        ('ELECTRICA', 'Eléctrica'), ('NEUMATICOS', 'Neumáticos'),
                        ('CHAPA_PINTURA', 'Chapa y pintura'), ('OTRO', 'Otro'),
                    ],
                    max_length=20,
                )),
                ('fecha', models.DateField()),
                ('descripcion', models.TextField(blank=True)),
                ('repuesto', models.CharField(blank=True, max_length=500)),
                ('quien_realizo', models.CharField(
                    blank=True,
                    choices=[
                        ('PERSONAL_PROPIO', 'Personal propio'),
                        ('TALLER', 'Taller mecánico'),
                        ('CONCESIONARIO', 'Concesionario oficial'),
                    ],
                    max_length=20,
                )),
                ('taller', models.CharField(blank=True, max_length=200)),
                ('cuit_taller', models.CharField(blank=True, max_length=20)),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('nro_factura', models.CharField(blank=True, max_length=100)),
                ('pago_realizado', models.BooleanField(default=False)),
                ('metodo_pago', models.CharField(
                    blank=True,
                    choices=[
                        ('CHEQUE', 'Cheque'), ('TRANSFERENCIA', 'Transferencia'),
                        ('TARJETA', 'Tarjeta'), ('EFECTIVO', 'Efectivo'),
                    ],
                    max_length=20,
                )),
                ('observaciones', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('cargado_por', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mantenimientos_cargados',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('maquinaria', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='mantenimientos',
                    to='chatbot.maquinaria',
                )),
            ],
            options={
                'verbose_name': 'Registro de Mantenimiento',
                'verbose_name_plural': 'Registros de Mantenimiento',
                'ordering': ['-fecha'],
            },
        ),
    ]
