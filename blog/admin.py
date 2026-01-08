from django.contrib import admin
from .models import Categoria, Articulo, SubCategoria, Tipo, Layout
from mainApp.admin_utils import DenyRedirectAdminMixin
from solo.admin import SingletonModelAdmin

@admin.register(Layout)
class SiteConfigAdmin(DenyRedirectAdminMixin, SingletonModelAdmin):
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff



from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

def _update_admin_titles():
    try:
        layout = Layout.get_solo()       # si usás django-solo
    except Exception:
        layout = Layout.objects.first()  # fallback
    title = getattr(layout, "titulo", "Asigne titulo en Layout")
    admin.site.site_header = title
    admin.site.site_title  = title
    admin.site.index_title = "Panel de gestión"  # o usa otro campo si lo tenés

# inicializa al cargar admin.py
_update_admin_titles()

# actualiza automáticamente cuando cambie/elimine el Layout
@receiver(post_save, sender=Layout)
@receiver(post_delete, sender=Layout)
def _refresh_admin_titles(*args, **kwargs):
    _update_admin_titles()
