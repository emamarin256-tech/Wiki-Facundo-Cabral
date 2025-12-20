from django.contrib import admin
from .models import Categoria, Articulo, SubCategoria, Tipo, Layout
from mainApp.admin_utils import DenyRedirectAdminMixin
from solo.admin import SingletonModelAdmin
# Register your models here.

# -----------------------
# Layout admin
# -----------------------
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



class CategoriaAdmin(DenyRedirectAdminMixin, admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff


class SubCategoriaAdmin(DenyRedirectAdminMixin, admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
class TipoAdmin(DenyRedirectAdminMixin, admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
        
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff


class ArticuloAdmin(DenyRedirectAdminMixin, admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion", "ultima_modificacion")

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
        
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if request.user.is_staff:
            return True
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff
    
    class Media:
        css = {
            'all': ('css/estilosAdmin.css',),
        }


admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Articulo, ArticuloAdmin)
admin.site.register(SubCategoria, SubCategoriaAdmin)
admin.site.register(Tipo, TipoAdmin)
