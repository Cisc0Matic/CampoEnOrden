from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User
from core.models import Persona, Campo, Lote, Campana, Labor


class TenancySmokeTest(TestCase):
    def setUp(self):
        self.principal = User.objects.create_user(
            username='principal', password='p', role=User.Role.ADMIN_PRINCIPAL, is_active=True,
        )
        self.empresa_a = Persona.objects.create(nombre='Empresa A', tipo=Persona.TipoPersona.EMPRESA, rol=Persona.Rol.PRODUCTOR)
        self.empresa_b = Persona.objects.create(nombre='Empresa B', tipo=Persona.TipoPersona.EMPRESA, rol=Persona.Rol.PRODUCTOR)

        self.admin_a = User.objects.create_user(
            username='admina', password='p', role=User.Role.ADMIN_EMPRESA,
            empresa=self.empresa_a, is_active=True,
        )
        self.prod_a_user = User.objects.create_user(
            username='proda', password='p', role=User.Role.PRODUCTOR,
            empresa=self.empresa_a, is_active=True,
        )
        self.prod_a_user.vincular_productor()
        self.productor_a = self.prod_a_user.persona

        self.productor_b = Persona.objects.create(
            nombre='Productor B', rol=Persona.Rol.PRODUCTOR, empresa=self.empresa_b
        )

        self.campo_a = Campo.objects.create(nombre='Campo A', productor=self.productor_a)
        self.campo_b = Campo.objects.create(nombre='Campo B', productor=self.productor_b, superficie_total=100)

        campana = Campana.objects.create(nombre='Campaña 1', activa=True, inicio='2026-01-01')
        self.lote_a = Lote.objects.create(nombre='Lote A', campo=self.campo_a, campana=campana, superficie=10)
        lote_b = Lote.objects.create(nombre='Lote B', campo=self.campo_b, campana=campana, superficie=20)
        Labor.objects.create(lote=self.lote_a, tipo='COSECHA', fecha='2026-01-01', hectareas=5, precio_por_ha=100)
        Labor.objects.create(lote=lote_b, tipo='SIEMBRA', fecha='2026-01-02', hectareas=5, precio_por_ha=100)

    def _auth(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_anonymos_no_access(self):
        res = APIClient().get('/api/core/campos/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_principal_ve_todo(self):
        res = self._auth(self.principal).get('/api/core/campos/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 2)

    def test_admin_empresa_solo_sus_campos(self):
        res = self._auth(self.admin_a).get('/api/core/campos/')
        self.assertEqual([c['id'] for c in res.json()], [self.campo_a.id])

    def test_productor_solo_sus_campos(self):
        res = self._auth(self.prod_a_user).get('/api/core/campos/')
        self.assertEqual([c['id'] for c in res.json()], [self.campo_a.id])
        lotes = self._auth(self.prod_a_user).get('/api/core/lotes/')
        self.assertEqual([l['id'] for l in lotes.json()], [self.lote_a.id])

    def test_labores_scoped(self):
        res = self._auth(self.prod_a_user).get('/api/core/labores/')
        data = res.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['lote'], self.lote_a.id)

    def test_personas_scoped_a_empresa(self):
        # La admin A ve su empresa y sus productores, pero no los de B
        personas = self._auth(self.admin_a).get('/api/core/personas/').json()
        ids = {p['id'] for p in personas}
        self.assertIn(self.productor_a.id, ids)
        self.assertIn(self.empresa_a.id, ids)
        self.assertNotIn(self.productor_b.id, ids)

    def test_productor_vincular_crea_persona(self):
        u = User.objects.create_user(
            username='prodb', password='p', role=User.Role.PRODUCTOR,
            empresa=self.empresa_b, first_name='Juan', last_name='Pérez', is_active=True,
        )
        u.vincular_productor()
        self.assertIsNotNone(u.persona)
        self.assertEqual(u.persona.rol, Persona.Rol.PRODUCTOR)
        self.assertEqual(u.persona.empresa, self.empresa_b)
        self.assertEqual(u.persona.pk, u.persona_id)

    def test_dashboard_scoped(self):
        res = self._auth(self.prod_a_user).get('/api/core/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['campos_activos'], 1)
        self.assertEqual(res.json()['labores_cargadas'], 1)

    def test_indicadores_403_ajeno(self):
        res = self._auth(self.admin_a).get(f'/api/core/dashboard/campo/{self.campo_b.id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_principal_puede_acotar_por_empresa(self):
        res = self._auth(self.principal).get(f'/api/core/campos/?empresa={self.empresa_a.id}')
        self.assertEqual([c['id'] for c in res.json()], [self.campo_a.id])
        res = self._auth(self.principal).get(f'/api/core/campos/?empresa={self.empresa_b.id}')
        self.assertEqual([c['id'] for c in res.json()], [self.campo_b.id])

    def test_empresa_no_puede_escapar_scope_con_parametro(self):
        res = self._auth(self.admin_a).get(f'/api/core/campos/?empresa={self.empresa_b.id}')
        self.assertEqual([c['id'] for c in res.json()], [self.campo_a.id])

    def test_dashboard_acotado_por_empresa(self):
        res = self._auth(self.principal).get(f'/api/core/dashboard/?empresa={self.empresa_b.id}')
        self.assertEqual(res.json()['campos_activos'], 1)
        self.assertEqual(res.json()['labores_cargadas'], 1)

    def test_empresa_detail_y_patch(self):
        client = self._auth(self.principal)
        get = client.get(f'/api/users/empresas/{self.empresa_a.id}/')
        self.assertEqual(get.status_code, 200)
        patch = client.patch(
            f'/api/users/empresas/{self.empresa_a.id}/',
            {'telefono': '3510000000'}, format='json',
        )
        self.assertEqual(patch.status_code, 200)
        self.empresa_a.refresh_from_db()
        self.assertEqual(self.empresa_a.telefono, '3510000000')

    def test_persona_creada_por_empresa_se_auto_vincula(self):
        res = self._auth(self.admin_a).post(
            '/api/core/personas/',
            {'nombre': 'Contratista X', 'rol': 'CONTRATISTA'}, format='json',
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json().get('empresa'), self.empresa_a.id)