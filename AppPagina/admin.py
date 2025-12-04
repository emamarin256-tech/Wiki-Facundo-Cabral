from django.contrib import admin
from .models import Pagina
# Register your models here.

#config panel
Titulo = "Wiki Facundo cabral"
Subtitulo = "Panel de gestión"

class PaginaAdmin(admin.ModelAdmin):
    
    readonly_fields = ("usuario", "creacion", "modificacion")

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario_id = request.user.id
        obj.save()
admin.site.site_header=Titulo
admin.site.site_title=Titulo
admin.site.index_title=Subtitulo

admin.site.register(Pagina, PaginaAdmin)