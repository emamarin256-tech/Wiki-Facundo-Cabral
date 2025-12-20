from django.contrib import admin
from .models import Pagina
from mainApp.admin_utils import DenyRedirectAdminMixin
# Register your models here.

#config panel
Titulo = "Wiki Facundo cabral"
Subtitulo = "Panel de gestión"

class PaginaAdmin(DenyRedirectAdminMixin, admin.ModelAdmin):
    
    readonly_fields = ("usuario", "creacion", "modificacion")

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
        
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff    
        
        
    class Media:
        css = {
            'all': ('css/estilosAdmin.css',),
        }
admin.site.site_header=Titulo
admin.site.site_title=Titulo
admin.site.index_title=Subtitulo

admin.site.register(Pagina, PaginaAdmin)