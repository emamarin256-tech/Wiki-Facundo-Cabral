from django.contrib import admin
from .models import Categoria, Articulo, SubCategoria, Tipo, Layout
from mainApp.admin_utils import DenyRedirectAdminMixin
from solo.admin import SingletonModelAdmin
from django.db.utils import OperationalError, ProgrammingError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@admin.register(Layout)
class SiteConfigAdmin(DenyRedirectAdminMixin, SingletonModelAdmin):
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

def _update_admin_titles():
    try:
        layout = Layout.get_solo()
    except Exception:
        try:
            layout = Layout.objects.first()
        except Exception:
            layout = None

    title = getattr(layout, "titulo", "Asigne titulo en Layout") if layout else "Asigne titulo en Layout"
    admin.site.site_header = title
    admin.site.site_title  = title
    admin.site.index_title = "Panel de gestión"

# evitar ejecutar durante migrate/creación de tablas: capturamos errores de DB
try:
    _update_admin_titles()
except (OperationalError, ProgrammingError):
    pass

@receiver(post_save, sender=Layout)
@receiver(post_delete, sender=Layout)
def _refresh_admin_titles(*args, **kwargs):
    try:
        _update_admin_titles()
    except (OperationalError, ProgrammingError):
        pass

