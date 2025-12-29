from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.messages import get_messages
from blog.models import Tipo
from AppPagina.models import Pagina


class PaginaModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="testpass123"
        )

        self.tipo = Tipo.objects.create(
            nombre="cancion",
            slug="cancion"
        )

        self.pagina = Pagina.objects.create(
            titulo="Prueba",
            contenido="Contenido de prueba",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=1,
            es_inicio=False,
        )

    def test_pagina_se_crea_correctamente(self):
        self.assertEqual(self.pagina.titulo, "Prueba")
        self.assertEqual(self.pagina.tipo.slug, "cancion")

    def test_slug_se_autogenera(self):
        self.assertIsNotNone(self.pagina.slug)
        self.assertEqual(self.pagina.slug, "prueba")

    def test_str_devuelve_titulo(self):
        self.assertEqual(str(self.pagina), "Prueba")

    def test_get_absolute_url(self):
        
        if self.pagina.slug:
            url = reverse("N_pagina", args=[self.pagina.slug])
            self.assertIn(self.pagina.slug, url)
        else:
            url = reverse("N_inicio")
            self.assertEqual(url, "/")





class PaginaURLsTest(TestCase):

    def test_resuelve_urls_correctamente(self):
        inicio = reverse("N_inicio")
        self.assertEqual(inicio, "/")

        detalle = reverse("N_pagina", args=["slug-ejemplo"])
        self.assertEqual(detalle, "/slug-ejemplo/")


class PaginaModelFullTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username="tester", password="testpass123")
        self.tipo = Tipo.objects.create(nombre="cancion", slug="cancion")

    def test_crear_pagina_inicio_tiene_slug_vacio_y_orden_0(self):
        p = Pagina.objects.create(
            titulo="Inicio A",
            contenido="Contenido",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )
        p.refresh_from_db()
        self.assertTrue(p.es_inicio)
        self.assertEqual(p.slug, "")
        self.assertEqual(p.orden, 0)

    def test_marcar_otra_pagina_como_inicio_desmarca_la_anterior_y_reasigna_slug_y_orden(self):
        
        p1 = Pagina.objects.create(
            titulo="Página Uno",
            contenido="Contenido",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )
        p1.refresh_from_db()
        self.assertTrue(p1.es_inicio)
        self.assertEqual(p1.slug, "")
        self.assertEqual(p1.orden, 0)

        
        p2 = Pagina.objects.create(
            titulo="Página Dos",
            contenido="Contenido 2",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p2.refresh_from_db()
        
        p2.es_inicio = True
        p2.save()

        
        p1.refresh_from_db()
        p2.refresh_from_db()

        
        self.assertTrue(p2.es_inicio)
        self.assertEqual(p2.slug, "")
        self.assertEqual(p2.orden, 0)

        
        self.assertFalse(p1.es_inicio)
        self.assertNotEqual(p1.slug, "")
        self.assertEqual(p1.slug, slugify(p1.titulo))
        self.assertEqual(p1.orden, 1)

    def test_al_crear_varias_paginas_inicio_el_ultimo_se_queda_como_inicio(self):
        p1 = Pagina.objects.create(
            titulo="Primera",
            contenido="c",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )
        p2 = Pagina.objects.create(
            titulo="Segunda",
            contenido="c2",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertFalse(p1.es_inicio)
        self.assertTrue(p2.es_inicio)
        self.assertEqual(p2.slug, "")
        self.assertEqual(p2.orden, 0)

    def test_titulos_duplicados_se_renombran_y_slug_se_genera_correctamente(self):
        p1 = Pagina.objects.create(
            titulo="Mismo Titulo",
            contenido="a",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p2 = Pagina.objects.create(
            titulo="Mismo Titulo",
            contenido="b",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertNotEqual(p1.titulo, p2.titulo)
        self.assertEqual(p2.titulo, "Mismo Titulo (1)")
        expected_slug_p2 = slugify(p2.titulo)
        self.assertEqual(p2.slug, expected_slug_p2)

    def test_slugs_unicos_si_hay_conflicto_se_agrega_sufijo(self):
        p1 = Pagina.objects.create(
            titulo="Prueba",
            contenido="c1",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p2 = Pagina.objects.create(
            titulo="Prueba",
            contenido="c2",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertEqual(p1.slug, "prueba")
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertEqual(p2.slug, "prueba-1")

    def test_str_devuelve_titulo_full(self):
        p = Pagina.objects.create(
            titulo="Mi Titulo",
            contenido="x",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        self.assertEqual(str(p), "Mi Titulo")

    def test_ordering_por_orden_y_creacion(self):
        a = Pagina.objects.create(
            titulo="A",
            contenido="x",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=5,
            es_inicio=False,
        )
        b = Pagina.objects.create(
            titulo="B",
            contenido="y",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=1,
            es_inicio=False,
        )
        c = Pagina.objects.create(
            titulo="C",
            contenido="z",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=3,
            es_inicio=False,
        )
        titulos_in_order = list(Pagina.objects.values_list("titulo", flat=True))
        self.assertEqual(titulos_in_order[0], "B")

class PaginaAdditionalTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="testpass123"
        )
        self.tipo = Tipo.objects.create(nombre="cancion", slug="cancion")

    def test_orden_min_value_validator(self):
        """Crear una Pagina con orden negativo debe fallar al full_clean()."""
        p = Pagina(
            titulo='Orden Negativo',
            contenido='x',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=-1,
        )
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_save_idempotent_slug_unchanged(self):
        """Guardar repetidamente la misma instancia no debe cambiar su slug original."""
        p = Pagina.objects.create(
            titulo='Guarda Idempotente',
            contenido='x',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=10,
        )
        original_slug = p.slug
        p.save()
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.slug, original_slug)

    def test_manual_duplicate_slug_either_resolved_or_raises(self):
        """Si se intenta crear una Pagina con slug explícito duplicado, la app
        debe o bien resolver el conflicto (modificando el slug) o lanzar IntegrityError.
        Este test acepta ambas opciones como válidas.
        """
        p1 = Pagina.objects.create(
            titulo='Primera',
            contenido='x',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=5,
            slug='slug-duplicado'
        )
        p2 = Pagina(
            titulo='Segunda',
            contenido='y',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=6,
            slug='slug-duplicado'
        )
        try:
            p2.save()
        except IntegrityError:
            return
        self.assertNotEqual(p2.slug, p1.slug, "El segundo objeto terminó con el mismo slug; se esperaba resolución o error.")
        self.assertEqual(p1.slug, "slug-duplicado")
        self.assertEqual(p2.slug, "slug-duplicado-1")


class PaginaViewsTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="testpass123"
        )

        self.tipo = Tipo.objects.create(
            nombre="general",
            slug="general"
        )

        self.pagina_inicio = Pagina.objects.create(
            titulo="Inicio",
            contenido="Contenido inicio",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )

        self.pagina_contenido = Pagina.objects.create(
            titulo="Página con contenido",
            contenido="Texto visible",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )

        self.pagina_sin_contenido = Pagina.objects.create(
            titulo="Página vacía",
            contenido="",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )


    def test_vista_inicio_responde_200(self):
        url = reverse("N_inicio")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_vista_inicio_usa_template_correcto(self):
        url = reverse("N_inicio")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "paginas/pag_inicio.html")

    def test_vista_inicio_envia_contexto_correcto(self):
        url = reverse("N_inicio")
        response = self.client.get(url)

        self.assertEqual(response.context["v_pag"], self.pagina_inicio)
        self.assertEqual(response.context["v_titulo"], "Inicio")
        self.assertTrue(response.context["v_pag_inicio"])

    def test_cargar_url_con_contenido_responde_200(self):
        url = reverse("N_pagina", args=[self.pagina_contenido.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_cargar_url_con_contenido_usa_template_correcto(self):
        url = reverse("N_pagina", args=[self.pagina_contenido.slug])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "paginas/pagina.html")

    def test_cargar_url_con_contenido_muestra_texto(self):
        url = reverse("N_pagina", args=[self.pagina_contenido.slug])
        response = self.client.get(url)
        self.assertContains(response, "Texto visible")

    def test_cargar_url_sin_contenido_redirige_a_inicio(self):
        url = reverse("N_pagina", args=[self.pagina_sin_contenido.slug])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("N_inicio"))

    def test_cargar_url_sin_contenido_muestra_mensaje_error(self):
        url = reverse("N_pagina", args=[self.pagina_sin_contenido.slug])
        response = self.client.get(url, follow=True)

        mensajes = list(get_messages(response.wsgi_request))
        self.assertEqual(len(mensajes), 1)
        self.assertIn("no tiene contenido cargado", mensajes[0].message)

    def test_cargar_url_slug_inexistente_devuelve_404(self):
        url = reverse("N_pagina", args=["slug-inexistente"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

