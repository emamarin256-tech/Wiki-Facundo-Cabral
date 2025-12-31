import subprocess
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from embed_video.fields import EmbedVideoField
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.files import File
import os
import cv2
from django.core.files.base import ContentFile
from solo.models import SingletonModel
# Create your models here.

class Layout(SingletonModel):

    class Meta:
        verbose_name = " Layout"
        verbose_name_plural = " Layout"


    titulo = models.CharField(max_length=200, default="Mi sitio")
    logo = models.ImageField(upload_to="images/", null=True, blank=True)
    def save(self, *args, **kwargs):
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).first()
            if old:
                # Si había logo y ahora no → borrar archivo
                if old.logo and not self.logo:
                    borrar_fieldfile(old.logo)
                # Si cambió el archivo → borrar el anterior
                elif old.logo and self.logo and old.logo.name != self.logo.name:
                    borrar_fieldfile(old.logo)

        super().save(*args, **kwargs)
    def __str__(self):
        return "Layout"
    
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre")
    desc = models.CharField(max_length=255,verbose_name='Descripción')
    creacion = models.DateTimeField(auto_now_add=True, blank=True,null=True)
    paginas = models.ManyToManyField("AppPagina.Pagina", verbose_name="Páginas", blank=True, related_name="categorias")
    publico = models.BooleanField(verbose_name="Publicado",default=True)
    usuario = models.ForeignKey(User, verbose_name="Usuario",editable=False ,on_delete=models.CASCADE,null=True)
    descripcion_modelo = """
    Las categorías se muestran cuando se pasa por encima de la página a la que pertenecen, en un menú desplegable de la barra de navegación.
    Normalmente mostrarán subcategorías; en caso de no tenerlas, mostrarán artículos. Si no hay nada de lo antes mencionado, se redirigirá a la página de inicio.  
    """
    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
    def save(self, *args, **kwargs):
        counter = 1
        base_nombre = self.nombre
        while Categoria.objects.filter(nombre=self.nombre).exclude(pk=self.pk).exists():
            self.nombre = f"{base_nombre} ({counter})"
            counter += 1
        super().save(*args, **kwargs)
    def __str__(self):
        return self.nombre




class SubCategoria(models.Model): 
    nombre = models.CharField(max_length=100)
    desc = models.CharField(max_length=255,verbose_name='Descripción',blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        verbose_name="Categoría",
        related_name="subcategorias",
        on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, blank=True, max_length=150,help_text="Si se deja vacío, se generará automáticamente a partir del nombre.")
    imagen = models.ImageField(verbose_name="Miniatura", upload_to="thumbnails/", blank=True, null="True")
    usar_miniatura = models.BooleanField(default=False,verbose_name="¿Usar miniatura?",help_text="Si marcás esto, indicarás si la miniatura que tenés cargada se verá o no. Si no hay una miniatura cargada, el sistema intentará obtenerla del vídeo después de guardar.")
    video_url = EmbedVideoField(blank=True, null=True,verbose_name="Video (URLS)")
    video_file = models.FileField(upload_to="videos/", blank=True, null=True, verbose_name="Videos (ARCHIVO)")
    publico = models.BooleanField(default=True)
    creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, verbose_name="Usuario",editable=False ,on_delete=models.CASCADE,null=True)
    
    descripcion_modelo = """Las subcategorías son visibles dentro de las categorías. Estas muestran los artículos que les pertenecen; en caso de no tenerlos, mostrarán su propio contenido.
    Este contenido deberá tener, como mínimo, la descripción o algún video para mostrar. Si no tienen contenido ni artículos que mostrar, la subcategoría no se mostrará."""
    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"

    def save(self, *args, **kwargs):
        counter = 1
        base_nombre = self.nombre
        while SubCategoria.objects.filter(nombre=self.nombre).exclude(pk=self.pk).exists():
            self.nombre = f"{base_nombre} ({counter})"
            counter += 1
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            while SubCategoria.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).first()
            if old:
                
                if getattr(old, 'imagen', None) and not getattr(self, 'imagen', None):
                    borrar_fieldfile(old.imagen)
                
                elif getattr(old, 'imagen', None) and getattr(self, 'imagen', None) and old.imagen.name != self.imagen.name:
                    borrar_fieldfile(old.imagen)

                
                if getattr(old, 'video_file', None) and not getattr(self, 'video_file', None):
                    borrar_fieldfile(old.video_file)
                elif getattr(old, 'video_file', None) and getattr(self, 'video_file', None) and old.video_file.name != self.video_file.name:
                    borrar_fieldfile(old.video_file)

        super().save(*args, **kwargs)
    
    def clean(self):
        super().clean()
        
        if self.video_url and self.video_file:
            raise ValidationError("Solo se permite 1 tipo de video: URL o ARCHIVO.")
    def __str__(self):
        return self.nombre



class Tipo(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True,max_length=150,help_text="Si se deja vacío, se generará automáticamente a partir del nombre.")
    publico = models.BooleanField(default=True)
    creacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, verbose_name="Usuario",editable=False ,on_delete=models.CASCADE,null=True)
    
    descripcion_modelo = """Los tipos relacionan las páginas con los artículos"""
    class Meta:
        verbose_name = "Tipo"
        verbose_name_plural = "Tipos"
    def save(self, *args, **kwargs):
        counter = 1
        base_nombre = self.nombre
        while Tipo.objects.filter(nombre=self.nombre).exclude(pk=self.pk).exists():
            self.nombre = f"{base_nombre} ({counter})"
            counter += 1

        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            while Tipo.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.nombre}"


class Articulo(models.Model):
    titulo = models.CharField(max_length=100,verbose_name='Título')
    contenido = RichTextField(max_length=1000, verbose_name="Contenido")
    imagen = models.ImageField(verbose_name="Miniatura", upload_to="thumbnails/", blank=True, null="True")
    usar_miniatura = models.BooleanField(default=False,verbose_name="¿Usar miniatura?", help_text="Si marcás esto, indicarás si la miniatura que tenés cargada se verá o no. Si no hay una miniatura cargada, el sistema intentará obtenerla del vídeo después de guardar.")
    video_url = EmbedVideoField(blank=True, null=True,verbose_name="Video (URLS)")
    video_file = models.FileField(upload_to="videos/", blank=True, null=True, verbose_name="Videos (ARCHIVO)")
    publico = models.BooleanField(verbose_name="Publicado")
    usuario = models.ForeignKey(User, verbose_name="Usuario",editable=False ,on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, verbose_name="Categorias", null=True, blank=True,on_delete=models.CASCADE)
    subcategoria = models.ForeignKey(SubCategoria, null=True, blank=True, on_delete=models.SET_NULL, related_name='articulos')
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE, related_name='articulos', null=True, blank=True)
    creacion = models.DateTimeField(auto_now_add=True , verbose_name="creación")
    ultima_modificacion = models.DateTimeField(auto_now=True,verbose_name="ultima modificación" )
    
    
    descripcion_modelo = """Los artículos son visibles dentro de una categoría y una subcategoría. Dependiendo del tipo, se mostrarán en una u otra página."""
    class Meta:
        verbose_name = "Artículo"
        verbose_name_plural = "Artículos"
        ordering = ['-creacion']
    
    def save(self, *args, **kwargs):
        counter = 1
        base_titulo = self.titulo
        while Articulo.objects.filter(titulo=self.titulo).exclude(pk=self.pk).exists():
            self.titulo = f"{base_titulo} ({counter})"
            counter += 1
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).first()
            if old:
                
                if getattr(old, 'imagen', None) and not getattr(self, 'imagen', None):
                    borrar_fieldfile(old.imagen)
                elif getattr(old, 'imagen', None) and getattr(self, 'imagen', None) and old.imagen.name != self.imagen.name:
                    borrar_fieldfile(old.imagen)

                
                if getattr(old, 'video_file', None) and not getattr(self, 'video_file', None):
                    borrar_fieldfile(old.video_file)
                elif getattr(old, 'video_file', None) and getattr(self, 'video_file', None) and old.video_file.name != self.video_file.name:
                    borrar_fieldfile(old.video_file)

        super().save(*args, **kwargs)
    
    def __str__(self):     
        
        return f"{self.titulo}"
    def clean(self):
        super().clean()
        
        if self.video_url and self.video_file:
            raise ValidationError("Solo se permite 1 tipo de video: URL o ARCHIVO.")
# region fun_miniatura_video
def crear_miniatura_video(instance):
    video_path = instance.video_file.path  
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
    ret, frame = cap.read()
    cap.release()

    if ret:
        _, buffer = cv2.imencode('.jpg', frame)
        # cv2.imencode usually returns a numpy array which has .tobytes(),
        # but in tests we may mock it to return plain bytes. Handle both.
        if hasattr(buffer, "tobytes"):
            data = buffer.tobytes()
        else:
            data = buffer

        instance.imagen.save(
            f"{instance.pk}_thumb.jpg",
            ContentFile(data),
            save=False
        )
        instance.save(update_fields=["imagen"])

@receiver(post_save, sender=Articulo)
def generar_miniatura_video_articulo(sender, instance, created, **kwargs):
    if instance.usar_miniatura and instance.video_file and not instance.imagen:
        crear_miniatura_video(instance)


@receiver(post_save, sender=SubCategoria)
def generar_miniatura_video_subcategoria(sender, instance, created, **kwargs):
    if instance.usar_miniatura and instance.video_file and not instance.imagen:
        crear_miniatura_video(instance)   
#endregion

# region fun_borrar_imagenes


def borrar_fieldfile(fieldfile):
    """
    Borra un FieldFile (ImageField/FileField) de forma segura.
    delete(save=False) usa el storage configurado (funciona con S3, GCS, local, etc).
    """
    try:
        if fieldfile and getattr(fieldfile, "name", None):
            fieldfile.delete(save=False)
    except Exception:
        # no romper el flujo por un fallo al borrar; opcional: loggear aquí
        pass

@receiver(post_delete, sender=Articulo)
def borrar_archivos_articulo_al_eliminar(sender, instance, **kwargs):
    borrar_fieldfile(getattr(instance, 'imagen', None))
    borrar_fieldfile(getattr(instance, 'video_file', None))

@receiver(post_delete, sender=SubCategoria)
def borrar_archivos_subcategoria_al_eliminar(sender, instance, **kwargs):
    borrar_fieldfile(getattr(instance, 'imagen', None))
    borrar_fieldfile(getattr(instance, 'video_file', None))

@receiver(post_delete, sender=Layout)
def borrar_logo_layout_al_eliminar(sender, instance, **kwargs):
    borrar_fieldfile(getattr(instance, 'logo', None))
#endregion