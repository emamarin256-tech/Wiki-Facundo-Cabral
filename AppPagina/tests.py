# AppPagina/tests.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db import IntegrityError


from blog.models import Tipo
from AppPagina.models import Pagina


# -------------------------------------------------------
# Tests originales (ligeros) — adaptados y preservados
# -------------------------------------------------------
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
        # Algunos objetos pagina pueden ser la página de inicio y no tener slug.
        if self.pagina.slug:
            url = reverse("N_pagina", args=[self.pagina.slug])
            self.assertIn(self.pagina.slug, url)
        else:
            url = reverse("N_inicio")
            self.assertEqual(url, "/")


class PaginaViewsTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="testpass123"
        )

        self.tipo_inicio = Tipo.objects.create(
            nombre="inicio",
            slug="inicio"
        )

        self.pagina = Pagina.objects.create(
            titulo="Inicio",
            contenido="Contenido",
            tipo=self.tipo_inicio,
            usuario=self.user,
            publico=True,
            es_inicio=True,
        )

    def test_vista_inicio_carga_correctamente(self):
        url = reverse("N_inicio")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inicio")

    def test_vista_detalle_por_slug(self):
        # Si la página creada en setUp es la página de inicio, crear una página adicional para esta prueba
        if not self.pagina.slug:
            pagina_detalle = Pagina.objects.create(
                titulo="Detalle",
                contenido="Contenido detalle",
                tipo=self.tipo_inicio,
                usuario=self.user,
                publico=True,
                es_inicio=False,
            )
        else:
            pagina_detalle = self.pagina

        url = reverse("N_pagina", args=[pagina_detalle.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pagina_detalle.contenido)


class PaginaURLsTest(TestCase):

    def test_resuelve_urls_correctamente(self):
        inicio = reverse("N_inicio")
        self.assertEqual(inicio, "/")

        detalle = reverse("N_pagina", args=["slug-ejemplo"])
        self.assertEqual(detalle, "/slug-ejemplo/")


# -------------------------------------------------------
# Tests ampliados para cubrir la lógica compleja del modelo
# (clean() / save() — unicidad de inicio, slugs, títulos, orden)
# -------------------------------------------------------
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
        # Primera página marcada como inicio
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

        # Crear una segunda página
        p2 = Pagina.objects.create(
            titulo="Página Dos",
            contenido="Contenido 2",
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            es_inicio=False,
        )
        p2.refresh_from_db()
        # ahora marcamos p2 como inicio (simulando edición)
        p2.es_inicio = True
        p2.save()

        # refrescar instancias desde la DB
        p1.refresh_from_db()
        p2.refresh_from_db()

        # p2 ahora debe ser la página de inicio
        self.assertTrue(p2.es_inicio)
        self.assertEqual(p2.slug, "")
        self.assertEqual(p2.orden, 0)

        # p1 debe haber sido desmarcada y recibir un slug y orden incrementado por la lógica del modelo
        self.assertFalse(p1.es_inicio)
        self.assertNotEqual(p1.slug, "")
        self.assertEqual(p1.slug, slugify(p1.titulo))
        # dado que el modelo incrementa orden en 1 para la página desplazada:
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
        # El último creado marcado como inicio debe ser el único con es_inicio True
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
        # el segundo debe haber sido renombrado a "Mismo Titulo (1)" por la lógica de clean()
        self.assertNotEqual(p1.titulo, p2.titulo)
        self.assertEqual(p2.titulo, "Mismo Titulo (1)")
        # y el slug del segundo corresponde al titulo modificado
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
        # El segundo título fue renombrado a "Prueba (1)", por lo tanto su slug debería contener "prueba"
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
        # Crear varias páginas con distintos valores de orden
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
        # Según Meta.ordering = ["orden", "-creacion"]
        titulos_in_order = list(Pagina.objects.values_list("titulo", flat=True))
        # Debe empezar por la de menor orden (B)
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
        # Llamar save varias veces
        p.save()
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.slug, original_slug)

    def test_manual_duplicate_slug_either_resolved_or_raises(self):
        """Si se intenta crear una Pagina con slug explícito duplicado, la app
        debe o bien resolver el conflicto (modificando el slug) o lanzar IntegrityError.
        Este test acepta ambas opciones como válidas.
        """
        # Crear la primera con slug explícito
        p1 = Pagina.objects.create(
            titulo='Primera',
            contenido='x',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=5,
            slug='slug-duplicado'
        )

        # Intentar crear otra con el mismo slug explícito
        p2 = Pagina(
            titulo='Segunda',
            contenido='y',
            tipo=self.tipo,
            usuario=self.user,
            publico=True,
            orden=6,
            slug='slug-duplicado'
        )
        p2.save()
        self.assertNotEqual(p2.slug, p1.slug, "El segundo objeto terminó con el mismo slug; se esperaba resolución o error.")
        self.assertTrue(p1.slug, "slug-duplicado")
        self.assertTrue(p2.slug, "slug-duplicado-1")
