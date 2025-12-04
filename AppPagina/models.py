from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
# Create your models here.

class Pagina(models.Model):
    titulo = models.CharField(verbose_name=("Título"), max_length=50)
    contenido = RichTextField(verbose_name="contenido",blank=True, null=True)
    orden=models.IntegerField(default=0,verbose_name="Orden", validators=[MinValueValidator(0)] )
    slug = models.SlugField(unique=True, max_length=150, verbose_name="URL_SLUG", blank=True, help_text="Si se deja vacío, se generará automáticamente a partir del título.")
    publico = models.BooleanField(verbose_name="Publicado")
    
    tipo = models.ForeignKey("blog.Tipo", on_delete=models.SET_NULL, verbose_name="Tipo de Artículo",
                             related_name="paginas", null=True, blank=True, help_text="Indica qué tipo de artículo se mostrará en las categorías o subcategorías de la página.")
    
    es_inicio = models.BooleanField(default=False, verbose_name="Página de inicio", help_text="Solo puede haber una página con esta opción. Al estar activa, el slug pasa a estar vacío y será la primera página en mostrarse.")
    
    
    creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    modificacion = models.DateTimeField(auto_now=True, verbose_name="Ultima modificación")
    usuario = models.ForeignKey(User, verbose_name="Usuario",editable=False ,on_delete=models.CASCADE, null=True)
    descripcion_modelo = """Las páginas son visibles en la barra de navegación. Si no tienen descripción, la página seguirá siendo visible en la barra de navegación, pero no se cargará su contenido y se redirigirá a la página de inicio.
    Las páginas pueden tener categorías, subcategorías y artículos."""
    
    class Meta:
        verbose_name = "Página"
        verbose_name_plural = "Páginas"
        ordering = ["orden", "-creacion"]  

    def clean(self):
        # --- Garantizar un solo inicio ---
        if self.es_inicio:
            Pagina.objects.exclude(pk=self.pk).update(es_inicio=False)
            self.slug = ""
            self.orden = 0
            counter = 1
            while Pagina.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                paginas = Pagina.objects.filter(slug=self.slug).exclude(pk=self.pk)
                for pagina in paginas:
                    base_slug = slugify(pagina.titulo) or "pagina"
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                    pagina.orden += 1 
                    Pagina.objects.filter(pk=pagina.pk).update(slug=slug , orden=pagina.orden)
            # Desmarcar otras páginas inicio
        else:
            # Evitar títulos duplicados
            base_titulo = self.titulo
            counter = 1
            while Pagina.objects.filter(titulo=self.titulo).exclude(pk=self.pk).exists():
                self.titulo = f"{base_titulo} ({counter})"
                counter += 1

            # Generar slug si no existe
            if not self.slug:
                base_slug = slugify(self.titulo) or "pagina"
                slug = base_slug
                counter = 1
                while Pagina.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug

    def save(self, *args, **kwargs):
        # llamar clean() aquí para que la lógica aplique también si guardas por código
        self.clean()

        # Si marcamos como inicio, desmarcar otras instancias (por seguridad)
        if self.es_inicio:
            Pagina.objects.exclude(pk=self.pk).update(es_inicio=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo or f"Página {self.pk}"