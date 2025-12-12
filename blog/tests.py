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



# Create your tests here.
