import tempfile
import shutil
import os
from unittest.mock import patch

import numpy as np
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import Categoria, SubCategoria, Tipo, Articulo

# Directorios temporales a nivel de módulo para usarse en los decoradores de clase.
# Se crean al importar el módulo y se eliminan en tearDownClass de cada clase.
SUBCAT_MEDIA_ROOT = tempfile.mkdtemp(prefix="test_media_subcat_")
ARTICLE_MEDIA_ROOT = tempfile.mkdtemp(prefix="test_media_article_")


class CategoriaModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="tester")

    def test_creacion_basica(self):
        c = Categoria.objects.create(
            nombre="Prueba",
            desc="Descripcion",
            usuario=self.user
        )
        self.assertEqual(c.nombre, "Prueba")
        self.assertEqual(str(c), "Prueba")

    def test_nombre_incremental(self):
        Categoria.objects.create(nombre="Noticias", desc="X", usuario=self.user)
        c2 = Categoria.objects.create(nombre="Noticias", desc="X", usuario=self.user)
        self.assertEqual(c2.nombre, "Noticias (1)")


@override_settings(MEDIA_ROOT=SUBCAT_MEDIA_ROOT)
class SubCategoriaModelTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(SUBCAT_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create(username="tester")
        self.categoria = Categoria.objects.create(
            nombre="General", desc="X", usuario=self.user
        )

    def test_slug_auto_generado(self):
        s = SubCategoria.objects.create(
            nombre="Mi Subcat",
            categoria=self.categoria,
            usuario=self.user
        )
        self.assertEqual(s.slug, "mi-subcat")

    def test_slug_incremental(self):
        SubCategoria.objects.create(
            nombre="Repetida",
            categoria=self.categoria,
            usuario=self.user
        )
        s2 = SubCategoria.objects.create(
            nombre="Repetida",
            categoria=self.categoria,
            usuario=self.user
        )
        self.assertIn("repetida", s2.slug)
        self.assertIn("1", s2.slug)

    def test_validacion_video_url_y_file(self):
        archivo = SimpleUploadedFile("video.mp4", b"12345", content_type="video/mp4")
        s = SubCategoria(
            nombre="Test",
            categoria=self.categoria,
            usuario=self.user,
            video_url="https://youtube.com/abc",
            video_file=archivo
        )
        with self.assertRaises(ValidationError):
            s.clean()

    @patch("cv2.VideoCapture")
    @patch("cv2.imencode")
    def test_signal_generar_miniatura(self, mock_imencode, mock_cap):
        # Mock de captura de video
        mock_cap.return_value.read.return_value = (
            True,
            np.zeros((100, 100, 3), dtype=np.uint8)
        )

        # Mock de imencode para que devuelva un buffer válido
        mock_imencode.return_value = (True, b"fakeimagebytes")

        archivo = SimpleUploadedFile("video.mp4", b"12345", content_type="video/mp4")

        s = SubCategoria.objects.create(
            nombre="VideoTest",
            categoria=self.categoria,
            usuario=self.user,
            usar_miniatura=True,
            video_file=archivo,
        )

        s.refresh_from_db()
        self.assertTrue(s.imagen)


class TipoModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="tester")

    def test_slug_auto_incremental(self):
        Tipo.objects.create(nombre="Texto", usuario=self.user)
        t2 = Tipo.objects.create(nombre="Texto", usuario=self.user)

        self.assertEqual(t2.nombre, "Texto (1)")
        self.assertIn("texto", t2.slug)

    def test_str(self):
        t = Tipo.objects.create(nombre="Musica", usuario=self.user)
        self.assertEqual(str(t), "Musica")


@override_settings(MEDIA_ROOT=ARTICLE_MEDIA_ROOT)
class ArticuloModelTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(ARTICLE_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create(username="tester")
        self.cat = Categoria.objects.create(nombre="Notas", desc="x", usuario=self.user)
        self.sub = SubCategoria.objects.create(
            nombre="Sub", categoria=self.cat, usuario=self.user
        )
        self.tipo = Tipo.objects.create(nombre="Tipo", usuario=self.user)

    def test_creacion_basica(self):
        a = Articulo.objects.create(
            titulo="Articulo Uno",
            contenido="Contenido",
            publico=True,
            usuario=self.user,
            categoria=self.cat,
            subcategoria=self.sub,
            tipo=self.tipo
        )
        self.assertEqual(str(a), "Articulo Uno")

    def test_titulo_incremental(self):
        Articulo.objects.create(
            titulo="Duplicado",
            contenido="x",
            publico=True,
            usuario=self.user
        )
        a2 = Articulo.objects.create(
            titulo="Duplicado",
            contenido="y",
            publico=True,
            usuario=self.user
        )
        self.assertEqual(a2.titulo, "Duplicado (1)")

    def test_validacion_video(self):
        archivo = SimpleUploadedFile("prueba.mp4", b"12345", content_type="video/mp4")
        a = Articulo(
            titulo="Vid",
            contenido="x",
            publico=True,
            usuario=self.user,
            video_url="http://url",
            video_file=archivo
        )
        with self.assertRaises(ValidationError):
            a.clean()

    @patch("cv2.VideoCapture")
    @patch("cv2.imencode")
    def test_signal_miniatura_video(self, mock_imencode, mock_cap):
        mock_cap.return_value.read.return_value = (
            True,
            np.zeros((100, 100, 3), dtype=np.uint8)
        )
        mock_imencode.return_value = (True, b"fakebytes")

        archivo = SimpleUploadedFile("video.mp4", b"12345", content_type="video/mp4")

        a = Articulo.objects.create(
            titulo="VideoArt",
            contenido="x",
            publico=True,
            usuario=self.user,
            usar_miniatura=True,
            video_file=archivo,
        )

        a.refresh_from_db()
        self.assertTrue(a.imagen)

    def test_ordenamiento_articulos(self):
        a1 = Articulo.objects.create(
            titulo="A1",
            contenido="x",
            publico=True,
            usuario=self.user
        )
        a2 = Articulo.objects.create(
            titulo="A2",
            contenido="x",
            publico=True,
            usuario=self.user
        )

        articulos = list(Articulo.objects.all())

        # A2 fue creado después, debería aparecer primero.
        self.assertEqual(articulos[0].titulo, "A2")
        self.assertEqual(articulos[1].titulo, "A1")


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from AppPagina.models import Pagina
# Asumo que estos modelos están en la misma app que las views (blog)
from .models import Categoria, SubCategoria, Articulo, Tipo

class BlogViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Crear Usuario y Tipos
        self.user = User.objects.create_user(username='testuser', password='password')
        self.tipo_video = Tipo.objects.create(nombre="Video", slug="video")
        self.tipo_noticia = Tipo.objects.create(nombre="Noticia", slug="noticia")
        
        # 2. Crear Páginas (Una de videos, una de noticias)
        self.pagina_video = Pagina.objects.create(
            titulo="Pagina Videos",
            slug="videos",
            tipo=self.tipo_video,
            usuario=self.user,
            publico=True,
            es_inicio=False,
            contenido="Contenido fallback"
        )
        
        self.pagina_noticia = Pagina.objects.create(
            titulo="Pagina Noticias",
            slug="noticias",
            tipo=self.tipo_noticia,
            usuario=self.user,
            publico=True,
            es_inicio=False,
            contenido=None # Sin contenido para probar redirección a inicio
        )
        # Página de inicio necesaria para redirecciones a 'N_inicio' en tests
        self.pagina_inicio = Pagina.objects.create(
            titulo="Inicio",
            slug="",
            tipo=self.tipo_noticia,
            usuario=self.user,
            publico=True,
            es_inicio=True,
            contenido="Contenido inicio"
        )

        # 3. Crear Categoría y Subcategoría
        self.categoria = Categoria.objects.create(nombre="Categoria General")
        # Asociar la categoría a la página de videos para que las plantillas puedan enlazarla
        self.categoria.paginas.add(self.pagina_video)
        
        # Subcategoría PÚBLICA con descripción (para pasar validación)
        self.subcat_valida = SubCategoria.objects.create(
            nombre="Subcat Valida",
            slug="subcat-valida",
            categoria=self.categoria,
            publico=True,
            desc="Descripción existente" 
        )
        
        # Subcategoría PRIVADA
        self.subcat_privada = SubCategoria.objects.create(
            nombre="Subcat Privada",
            slug="subcat-privada",
            categoria=self.categoria,
            publico=False,
            desc="Descripción existente"
        )

        # 4. Crear Artículos
        # Artículo que coincide con Pagina Videos y Subcat Valida
        self.articulo_video = Articulo.objects.create(
            titulo="Articulo Video",
            subcategoria=self.subcat_valida,
            categoria=self.categoria,
            tipo=self.tipo_video,
            publico=True,
            usuario=self.user
        )
        
        # Artículo de tipo diferente (Noticia) en la misma subcategoría
        self.articulo_noticia = Articulo.objects.create(
            titulo="Articulo Noticia",
            subcategoria=self.subcat_valida,
            categoria=self.categoria,
            tipo=self.tipo_noticia, # TIPO DIFERENTE A LA PAGINA
            publico=True,
            usuario=self.user
        )

    # ---------------------------------------------------------------
    # TEST: cargar_Pcategorias (La vista más compleja)
    # ---------------------------------------------------------------
    
    def test_cargar_categorias_con_subcategoria_valida(self):
        """
        Debe renderizar la categoría mostrando las subcategorías que pasaron la validación.
        """
        url = reverse("N_categoria", args=[self.pagina_video.slug, self.categoria.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'categorias/categoria.html')
        # Debe contener la subcategoría válida
        self.assertContains(response, "Subcat Valida")
        # NO debe contener la privada
        self.assertNotContains(response, "Subcat Privada")

    def test_cargar_categorias_vacia_redirecciona(self):
        """
        Si la categoría no tiene subcategorías ni artículos válidos para ese TIPO de página,
        debe redirigir a N_pagina (si tiene contenido) o N_inicio.
        """
        # Creamos una categoría vacía
        cat_vacia = Categoria.objects.create(nombre="Vacia")
        cat_vacia.paginas.add(self.pagina_video)
        
        # Caso A: La página tiene contenido -> Redirige a N_pagina
        url = reverse("N_categoria", args=[self.pagina_video.slug, cat_vacia.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("N_pagina", args=[self.pagina_video.slug]))
        
        # Caso B: La página NO tiene contenido -> Redirige a N_inicio con error
        url_noticia = reverse("N_categoria", args=[self.pagina_noticia.slug, cat_vacia.id])
        response_noticia = self.client.get(url_noticia, follow=True)
        self.assertRedirects(response_noticia, reverse("N_inicio"))
        # Verificar mensaje de error en la respuesta final después de seguir la redirección
        messages = list(response_noticia.context['messages'])
        self.assertTrue(any("No se han cargado elementos" in str(m) for m in messages))

    def test_cargar_categorias_sin_subcat_pero_con_articulos(self):
        """
        Si no hay subcategorías, pero hay artículos sueltos que coinciden con el tipo de página,
        debe renderizarlos.
        """
        # Crear categoría solo con artículos, sin subcategorías
        cat_solo_art = Categoria.objects.create(nombre="Solo Articulos")
        cat_solo_art.paginas.add(self.pagina_video)
        Articulo.objects.create(
            titulo="Articulo Suelto",
            categoria=cat_solo_art,
            tipo=self.tipo_video, # Coincide con pagina_video
            publico=True,
            usuario=self.user
        )
        
        url = reverse("N_categoria", args=[self.pagina_video.slug, cat_solo_art.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Articulo Suelto")

    def test_cargar_categorias_404_datos_incorrectos(self):
        """Si el slug de página o ID de categoría no existen, redirige a inicio."""
        url = reverse("N_categoria", args=["slug-falso", 999])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("N_inicio"))

    # ---------------------------------------------------------------
    # TEST: validacion_subcategoria (Indirecto)
    # ---------------------------------------------------------------
    
    def test_subcategoria_valida_por_articulos(self):
        """
        Prueba la lógica específica de 'validacion_subcategoria':
        Una subcategoría sin descripción/video pero CON artículos válidos debería mostrarse.
        """
        sub_sin_desc = SubCategoria.objects.create(
            nombre="Sin Descripcion",
            slug="sin-desc",
            categoria=self.categoria,
            publico=True,
            desc="" # Vacio
        )
        # Agregamos artículo para que pase la validación articulos.exists()
        Articulo.objects.create(
            titulo="Articulo Salvador",
            subcategoria=sub_sin_desc,
            tipo=self.tipo_video,
            publico=True,
            usuario=self.user
        )
        
        url = reverse("N_categoria", args=[self.pagina_video.slug, self.categoria.id])
        response = self.client.get(url)
        self.assertContains(response, "Sin Descripcion")

    # ---------------------------------------------------------------
    # TEST: cargar_Psubcategorias
    # ---------------------------------------------------------------

    def test_subcategoria_filtra_por_tipo_pagina(self):
        """
        En la vista de subcategoría, solo deben verse los artículos 
        que coinciden con el 'tipo' de la Pagina actual.
        """
        url = reverse("N_subcategoria", args=[self.pagina_video.slug, self.subcat_valida.slug])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Debe ver el artículo tipo Video
        self.assertContains(response, "Articulo Video")
        # NO debe ver el artículo tipo Noticia (aunque esté en la misma subcategoría)
        self.assertNotContains(response, "Articulo Noticia")

    # ---------------------------------------------------------------
    # TEST: cargar_Darticulo
    # ---------------------------------------------------------------

    def test_detalle_articulo_exito(self):
        url = reverse("N_articulo", args=[self.pagina_video.slug, self.articulo_video.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Articulo Video")

    def test_detalle_articulo_tipo_incorrecto(self):
        """
        Intentar ver un artículo de tipo 'Noticia' a través de una página de tipo 'Video' 
        debe fallar (redirigir a inicio según el try/except de la vista).
        """
        # pagina_video es tipo Video, articulo_noticia es tipo Noticia
        url = reverse("N_articulo", args=[self.pagina_video.slug, self.articulo_noticia.id])
        response = self.client.get(url)
        
        # Al no encontrar el artículo con ese filtro de tipo, entra al except y redirige
        self.assertRedirects(response, reverse("N_inicio"))
        
        
        
        
# Create your tests here.
