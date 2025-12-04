from django.contrib import admin
from .models import Categoria, Articulo, SubCategoria, Tipo
# Register your models here.


class CategoriaAdmin(admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()


class SubCategoriaAdmin(admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()

class TipoAdmin(admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion",)

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()


class ArticuloAdmin(admin.ModelAdmin):
    readonly_fields = ("usuario", "creacion", "ultima_modificacion")

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()


admin.site.register(Categoria, CategoriaAdmin)
admin.site.register(Articulo, ArticuloAdmin)
admin.site.register(SubCategoria, SubCategoriaAdmin)
admin.site.register(Tipo, TipoAdmin)
