from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError


def _generate_unique_slug(model, base_slug, exclude_pk=None):
    base = base_slug or "pagina"
    candidate = base
    counter = 1
    while model.objects.filter(slug=candidate).exclude(pk=exclude_pk).exists():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate
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
        """Validaciones sin efectos secundarios de BD.
        No se deben realizar updates sobre otras instancias aquí; esa lógica
        se mueve a `save()` para evitar efectos inesperados.
        """
        # Evitar títulos duplicados: renombrar añadiendo sufijo numérico si hace falta
        base_titulo = self.titulo
        counter = 1
        while Pagina.objects.filter(titulo=self.titulo).exclude(pk=self.pk).exists():
            self.titulo = f"{base_titulo} ({counter})"
            counter += 1

        # Generar slug candidato único y asignarlo a self (sin tocar otras filas)
        if self.slug:
            self.slug = _generate_unique_slug(Pagina, self.slug, exclude_pk=self.pk)
        else:
            base_slug = slugify(self.titulo) or "pagina"
            self.slug = _generate_unique_slug(Pagina, base_slug, exclude_pk=self.pk)

    def save(self, *args, **kwargs):
        # llamar clean() aquí para que la lógica aplique también si guardas por código
        self.clean()

        # Usar una transacción para evitar condiciones de carrera al reasignar slugs
        with transaction.atomic():
            if self.es_inicio:
                Pagina.objects.exclude(pk=self.pk).update(es_inicio=False)
                self.slug = ""
                self.orden = 0

                # Reasignar slugs a las páginas que tenían slug vacío (excluyendo esta)
                paginas = Pagina.objects.filter(slug="").exclude(pk=self.pk)
                for pagina in paginas:
                    base_slug = slugify(pagina.titulo) or "pagina"
                    candidate = _generate_unique_slug(Pagina, base_slug, exclude_pk=pagina.pk)
                    pagina.orden += 1
                    Pagina.objects.filter(pk=pagina.pk).update(slug=candidate, orden=pagina.orden)
            else:
                # Asegurar que `self.slug` ya sea único (clean() normalmente lo dejó así)
                if not self.slug:
                    self.slug = _generate_unique_slug(Pagina, slugify(self.titulo) or "pagina", exclude_pk=self.pk)

            try:
                super().save(*args, **kwargs)
            except IntegrityError:
                # Reintentar una vez generando un slug alternativo por seguridad
                self.slug = _generate_unique_slug(Pagina, slugify(self.titulo) or "pagina", exclude_pk=self.pk)
                super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo or f"Página {self.pk}"