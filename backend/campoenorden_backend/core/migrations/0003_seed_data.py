from django.db import migrations


def create_initial_data(apps, schema_editor):
    TipoLaborPersonalizado = apps.get_model('core', 'TipoLaborPersonalizado')
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    tipos_iniciales = [
        'Labranza',
        'Rolado',
        'Nivelación',
        'Monitoreo',
        'Limpieza de alambrado',
        'Aplicación manual',
        'Riego',
        'Control de malezas manual',
    ]
    for nombre in tipos_iniciales:
        TipoLaborPersonalizado.objects.get_or_create(nombre=nombre)

    app_models = {
        'core': ['campo', 'persona', 'campana', 'lote', 'cultivo',
                 'insumo', 'productoprecio', 'tipolaborpersonalizado',
                 'labor', 'laborinsumo', 'flete', 'documento', 'parametro'],
        'users': ['user'],
    }

    def get_perm(codename):
        for app_label, models in app_models.items():
            for model in models:
                if codename.endswith(f'_{model}'):
                    try:
                        ct = ContentType.objects.get(app_label=app_label, model=model)
                        return Permission.objects.get(codename=codename, content_type=ct)
                    except (ContentType.DoesNotExist, Permission.DoesNotExist):
                        continue
        return None

    roles = [
        {
            'name': 'Admin Principal',
            'perms': [
                'add_campo', 'change_campo', 'delete_campo', 'view_campo',
                'add_persona', 'change_persona', 'delete_persona', 'view_persona',
                'add_lote', 'change_lote', 'delete_lote', 'view_lote',
                'add_labor', 'change_labor', 'delete_labor', 'view_labor',
                'add_laborinsumo', 'change_laborinsumo', 'delete_laborinsumo', 'view_laborinsumo',
                'add_insumo', 'change_insumo', 'delete_insumo', 'view_insumo',
                'add_productoprecio', 'change_productoprecio', 'delete_productoprecio', 'view_productoprecio',
                'add_tipolaborpersonalizado', 'change_tipolaborpersonalizado', 'delete_tipolaborpersonalizado', 'view_tipolaborpersonalizado',
                'add_flete', 'change_flete', 'delete_flete', 'view_flete',
                'add_documento', 'change_documento', 'delete_documento', 'view_documento',
                'add_parametro', 'change_parametro', 'delete_parametro', 'view_parametro',
                'add_user', 'change_user', 'delete_user', 'view_user',
                'add_campana', 'change_campana', 'delete_campana', 'view_campana',
                'add_cultivo', 'change_cultivo', 'delete_cultivo', 'view_cultivo',
            ],
        },
        {
            'name': 'Admin de Empresa',
            'perms': [
                'add_campo', 'change_campo', 'view_campo',
                'add_persona', 'change_persona', 'view_persona',
                'add_lote', 'change_lote', 'view_lote',
                'add_labor', 'change_labor', 'view_labor',
                'add_laborinsumo', 'change_laborinsumo', 'view_laborinsumo',
                'add_insumo', 'change_insumo', 'view_insumo',
                'add_productoprecio', 'change_productoprecio', 'view_productoprecio',
                'add_tipolaborpersonalizado', 'change_tipolaborpersonalizado', 'view_tipolaborpersonalizado',
                'view_flete',
                'add_documento', 'change_documento', 'view_documento',
                'view_parametro',
                'view_user',
                'view_campana',
                'view_cultivo',
            ],
        },
        {
            'name': 'Operario',
            'perms': [
                'add_labor', 'change_labor', 'view_labor',
                'add_laborinsumo', 'change_laborinsumo', 'view_laborinsumo',
                'view_campo', 'view_lote', 'view_cultivo',
                'view_insumo', 'view_productoprecio',
                'view_tipolaborpersonalizado',
            ],
        },
        {
            'name': 'Usuario de Consulta',
            'perms': [
                'view_campo', 'view_lote', 'view_cultivo',
                'view_labor', 'view_laborinsumo',
                'view_insumo', 'view_productoprecio',
                'view_tipolaborpersonalizado',
                'view_parametro',
            ],
        },
        {
            'name': 'Cliente / Productor',
            'perms': [
                'view_campo', 'view_lote', 'view_cultivo',
                'view_labor', 'view_laborinsumo',
                'view_insumo', 'view_productoprecio',
            ],
        },
    ]

    for role in roles:
        group, created = Group.objects.get_or_create(name=role['name'])
        for codename in role['perms']:
            perm = get_perm(codename)
            if perm:
                group.permissions.add(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_tipolaborpersonalizado_campo_localidad_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]
