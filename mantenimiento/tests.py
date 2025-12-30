from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from mantenimiento import services
from blog.models import Categoria, Layout, Articulo
from mainApp.models import Rol, PerfilUsuario
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
import mainApp.signals as msignals
User = get_user_model()


# ==========================
# TESTS PARA SERVICES
# ==========================
class ServicesTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.categoria_model = services.get_model_by_name('Categoria')

    def test_get_model_by_name(self):
        self.assertEqual(
            services.get_model_by_name('categoria'),
            self.categoria_model
        )
        with self.assertRaises(LookupError):
            services.get_model_by_name('no_existe')

    def test_list_models(self):
        names = {m.__name__ for m in services.list_models()}
        self.assertIn('Categoria', names)
        self.assertIn('Layout', names)

    def test_build_allowed_fields(self):
        allowed = services.build_allowed_fields(Categoria)
        self.assertIn('nombre', allowed)
        self.assertIn('creacion', allowed)
        self.assertNotIn('desc', allowed)

    def test_queryset_search_and_sort(self):
        Categoria.objects.create(nombre='AAA')
        Categoria.objects.create(nombre='BBB')

        qs, _, _, _ = services.build_queryset_and_metadata(Categoria, 'A', '', '')
        self.assertEqual(qs.count(), 1)

        qs, campo, _, _ = services.build_queryset_and_metadata(Categoria, '', 'nombre', 'asc')
        self.assertEqual(campo, 'nombre')

    def test_create_form_widgets(self):
        Form = services.create_modelform_with_widgets(Articulo)
        form = Form()
        self.assertIn('contenido', form.fields)
        self.assertTrue(hasattr(form.fields['contenido'].widget, 'render'))


# ==========================
# TESTS DE VISTAS (MANTENIMIENTO)
# ==========================
class ViewsMaintenanceLayoutTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        rol, _ = Rol.objects.get_or_create(nombre='Usuario')
        cls.user = User.objects.create_user(
            username='tester',
            password='pwd'
        )
        PerfilUsuario.objects.get_or_create(
            user=cls.user,
            defaults={'rol': rol}
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='tester', password='pwd')

    def test_f_mantenimiento_ok(self):
        resp = self.client.get(reverse('N_mantenimiento'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('layo', resp.context)
        self.assertIn('lista_modelos', resp.context)

    def test_mantenimientoB_invalid_model(self):
        resp = self.client.get(reverse('N_mantenimientoB', args=['no_modelo']))
        self.assertEqual(resp.status_code, 302)

    def test_mantenimientoC_delete_categoria(self):
        cat = Categoria.objects.create(nombre='Eliminar')
        url = reverse('N_mantenimientoC', args=['categoria', cat.pk])

        self.client.post(url, {'accion': 'eliminar'})
        self.assertFalse(Categoria.objects.filter(pk=cat.pk).exists())

    def test_layout_cannot_be_deleted(self):
        layout = Layout.get_solo()
        url = reverse('N_mantenimientoC', args=['layout', layout.pk])

        resp = self.client.post(url, {'accion': 'eliminar'})
        self.assertTrue(Layout.objects.filter(pk=layout.pk).exists())

    def test_eliminar_varios(self):
        c1 = Categoria.objects.create(nombre='A')
        c2 = Categoria.objects.create(nombre='B')

        url = reverse('N_eliminar_varios', args=['categoria'])
        self.client.post(url, {'seleccionados': [c1.pk, c2.pk]})

        self.assertFalse(Categoria.objects.exists())


class RolRequiredDecoratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        
        
        try:
            post_save.disconnect(msignals.create_profile_on_user_create, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(msignals.assign_staff_role_to_superuser, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(msignals.sync_is_staff_with_rol, sender=PerfilUsuario)
        except Exception:
            pass

        
        cls.rol_usuario = Rol.objects.create(nombre='Usuario')
        cls.rol_otro = Rol.objects.create(nombre='Otro')
        
        Rol.objects.get_or_create(nombre='Staff')

        
        cls.no_perfil_user = User.objects.create_user(username='noperfil_test', password='pwd1')
        cls.user_otro = User.objects.create_user(username='otro_test', password='pwd2')
        cls.user_allowed = User.objects.create_user(username='allowed_test', password='pwd3')
        cls.superuser = User.objects.create_superuser(username='admin_test', password='adminpwd', email='admin@example.com')

        
        
        PerfilUsuario.objects.update_or_create(user=cls.user_otro, defaults={'rol': cls.rol_otro})
        PerfilUsuario.objects.update_or_create(user=cls.user_allowed, defaults={'rol': cls.rol_usuario})
        
        staff_rol, _ = Rol.objects.get_or_create(nombre='Staff')
        PerfilUsuario.objects.update_or_create(user=cls.superuser, defaults={'rol': staff_rol})

    @classmethod
    def tearDownClass(cls):
        
        try:
            post_save.connect(msignals.create_profile_on_user_create, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(msignals.assign_staff_role_to_superuser, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(msignals.sync_is_staff_with_rol, sender=PerfilUsuario)
        except Exception:
            pass

        super().tearDownClass()

    def setUp(self):
        self.client = Client()
        self.url = reverse('N_mantenimiento')  

    def test_unauthenticated_redirects_to_login_with_next(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        login_url = reverse('N_inicio_sesion')
        self.assertIn(login_url, resp['Location'])
        self.assertIn('next=', resp['Location'])

    def test_user_without_perfil_redirects_to_inicio_and_shows_message(self):
        self.client.login(username='noperfil_test', password='pwd1')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('N_inicio'))
        msgs = list(get_messages(resp.wsgi_request))
        self.assertTrue(any('espera' in str(m).lower() or 'aceptado' in str(m).lower() for m in msgs),
                        f"Mensajes esperados, pero recibió: {[str(m) for m in msgs]}")

    def test_user_with_disallowed_role_redirects_and_shows_no_permission_message(self):
        self.client.login(username='otro_test', password='pwd2')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('N_inicio'))
        msgs = list(get_messages(resp.wsgi_request))
        self.assertTrue(any('no tienes permiso' in str(m).lower() or 'permiso' in str(m).lower() for m in msgs),
                        f"Mensajes esperados, pero recibió: {[str(m) for m in msgs]}")

    def test_user_with_allowed_role_gets_200(self):
        self.client.login(username='allowed_test', password='pwd3')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.wsgi_request.user.username, 'allowed_test')

    def test_superuser_gets_200(self):
        self.client.login(username='admin_test', password='adminpwd')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.wsgi_request.user.is_superuser)


