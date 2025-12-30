from unittest.mock import patch

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.db import DatabaseError
from django.contrib.messages import get_messages

from mantenimiento import services
from blog.models import Categoria, Layout, Articulo
from mainApp.models import Rol, PerfilUsuario
from django.contrib.auth import get_user_model

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

