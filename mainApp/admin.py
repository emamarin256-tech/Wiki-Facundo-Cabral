from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import Layout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

# ========================
# ADMIN DEL LAYOUT
# ========================
@admin.register(Layout)
class SiteConfigAdmin(SingletonModelAdmin):
    pass


# ========================
# ADMIN DEL USUARIO
# ========================
User = get_user_model()

# 🔹 Desregistrar el admin original del modelo User
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


# 🔹 Registrar tu versión personalizada
@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff','is_superuser', 'mostrar_grupos')
    list_filter = ('groups', 'is_staff', 'is_superuser', 'is_active')
    actions = ['aprobar_usuarios']

    def mostrar_grupos(self, obj):
        return ", ".join([g.name for g in obj.groups.all()]) or "—"

    mostrar_grupos.short_description = "Grupos"

    def aprobar_usuarios(self, request, queryset):
        grupo_ingresante, _ = Group.objects.get_or_create(name='Ingresantes')
        grupo_usuario, _ = Group.objects.get_or_create(name='Usuarios')

        count = 0
        for user in queryset:
            user.groups.remove(grupo_ingresante)
            user.groups.add(grupo_usuario)
            user.save()
            count += 1

        self.message_user(request, f"{count} usuario(s) aprobados correctamente.")

