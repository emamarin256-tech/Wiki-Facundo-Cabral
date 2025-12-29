from django.test import TestCase, RequestFactory
from django.test import Client
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from .models import Rol, PerfilUsuario
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from .middleware import RedirectNoStaff, RangeRequestMiddleware
from importlib import import_module
from django.db.models.signals import post_save

User = get_user_model()

class ModelsTest(TestCase):
    def setUp(self):
        self.rol = Rol.objects.create(nombre='Ingresante', descripcion='Rol de prueba')

    def test_rol_str(self):
        self.assertEqual(str(self.rol), 'Ingresante')

    def test_perfilusuario_str_and_protect(self):
        user = User.objects.create_user(username='u1', password='pass123')
        perfil, _ = PerfilUsuario.objects.get_or_create(user=user, defaults={'rol': self.rol})
        self.assertEqual(str(perfil), f'{user.username} - {self.rol.nombre}')

        
        with self.assertRaises(ProtectedError):
            self.rol.delete()



User = get_user_model()

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.rol_ingresante = Rol.objects.create(nombre='Ingresante')
        try:
            self.f_registro_url = reverse('N_registro')
        except Exception:
            self.f_registro_url = '/registro/'
        self.f_inicio_sesion = reverse('N_inicio_sesion')
        self.f_usuario = reverse('N_usuario')
        self.f_cerrar = reverse('N_cerrar_sesion')

    def test_registro_crea_usuario_y_perfil(self):
        data = {
            'username': 'nuevo',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'email': 'n@e.com',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }
        resp = self.client.post(self.f_registro_url, data, follow=True)
        user = User.objects.filter(username='nuevo').first()
        self.assertIsNotNone(user, "El usuario no fue creado")
        perfil = getattr(user, 'perfil', None)
        self.assertIsNotNone(perfil, "No se creó PerfilUsuario")
        self.assertEqual(perfil.rol.nombre, 'Ingresante')

    def test_inicio_sesion_valido_e_invalid(self):
        user = User.objects.create_user(username='u2', password='pwd12345')
        resp = self.client.post(self.f_inicio_sesion, {'username': 'u2', 'password': 'pwd12345'}, follow=True)
        self.assertTrue(resp.context['user'].is_authenticated)
        self.client.logout()
        resp2 = self.client.post(self.f_inicio_sesion, {'username': 'u2', 'password': 'wrong'}, follow=True)
        self.assertFalse(resp2.context['user'].is_authenticated)

    def test_f_cerrar_sesion(self):
        user = User.objects.create_user(username='u3', password='pwd12345')
        self.client.login(username='u3', password='pwd12345')
        resp = self.client.get(self.f_cerrar, follow=True)
        self.assertFalse('_auth_user_id' in self.client.session)

User = get_user_model()

class UsuarioViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('N_usuario')
        self.login_url = reverse('N_inicio_sesion')

    def test_redirige_si_no_autenticado_con_next(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(self.login_url, resp['Location'])
        self.assertIn('next=', resp['Location'])

    def test_acceso_si_autenticado(self):
        user = User.objects.create_user(username='perm', password='12345')
        self.client.login(username='perm', password='12345')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


User = get_user_model()

class MiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.login_url = reverse('N_inicio_sesion')
        self.get_response = lambda req: HttpResponse("OK")
    def _attach_messages(self, request):
        session_mw = SessionMiddleware(self.get_response)
        session_mw.process_request(request)
        try:
            request.session.save()
        except Exception:
            pass
        setattr(request, '_messages', FallbackStorage(request))
    def test_redirect_no_staff_anonymous(self):
        request = self.factory.get('/admin/')
        request.user = type('U', (), {'is_authenticated': False, 'is_staff': False, 'is_superuser': False})()
        self._attach_messages(request)
        middleware = RedirectNoStaff(self.get_response)
        resp = middleware(request)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(self.login_url, resp['Location'])
    def test_redirect_no_staff_non_privileged_user(self):
        request = self.factory.get('/admin/')
        request.user = type('U', (), {'is_authenticated': True, 'is_staff': False, 'is_superuser': False})()
        self._attach_messages(request)
        middleware = RedirectNoStaff(self.get_response)
        resp = middleware(request)
        self.assertEqual(resp.status_code, 302)
    def test_range_request_middleware_adds_header(self):
        request = self.factory.get('/media/somefile.jpg')
        request.user = type('U', (), {'is_authenticated': True})()
        self._attach_messages(request)
        middleware = RangeRequestMiddleware(self.get_response)
        resp = middleware(request)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Accept-Ranges'], 'bytes')



User = get_user_model()

class SignalsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rol_ingresante, _ = Rol.objects.get_or_create(nombre='Ingresante')
        cls.rol_staff, _ = Rol.objects.get_or_create(nombre='Staff')
        import_module('mainApp.signals')

    def test_create_profile_signal_is_connected(self):
        import mainApp.signals as signals_mod

        
        
        self.assertTrue(post_save.has_listeners(User), "No hay listeners registrados para post_save(User).")

        
        self.assertTrue(
            hasattr(signals_mod, 'create_profile_on_user_create'),
            "El módulo mainApp.signals no define 'create_profile_on_user_create'."
        )

    def test_profile_created_on_user_create(self):
        user = User.objects.create_user(username='signal_user', password='password123')
        perfiles = PerfilUsuario.objects.filter(user=user)
        self.assertTrue(perfiles.exists())
        self.assertEqual(perfiles.count(), 1)
        self.assertEqual(perfiles.first().rol.nombre, 'Ingresante')

    def test_sync_is_staff_with_rol(self):
        user = User.objects.create_user(username='staff_test', password='password123')
        perfil = PerfilUsuario.objects.get(user=user)
        perfil.rol = self.rol_staff
        perfil.save()
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        perfil.rol = self.rol_ingresante
        perfil.save()
        user.refresh_from_db()
        self.assertFalse(user.is_staff)

    def test_assign_staff_role_to_superuser(self):
        superuser = User.objects.create_superuser(username='admin', email='a@b.c', password='password123')
        perfil = PerfilUsuario.objects.filter(user=superuser).select_related('rol').first()
        self.assertIsNotNone(perfil)
        self.assertEqual(perfil.rol.nombre, 'Staff')
        superuser.refresh_from_db()
        self.assertTrue(superuser.is_staff)
