from django.contrib import admin
from solo.admin import SingletonModelAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.contrib.auth.forms import AdminPasswordChangeForm
import secrets

from .models import Layout

# -----------------------
# Layout admin
# -----------------------
@admin.register(Layout)
class SiteConfigAdmin(SingletonModelAdmin):
    pass


class SafeAdminPasswordChangeForm(AdminPasswordChangeForm):
    """Form de cambio de contraseña usado por el admin que elimina
    la opción peligrosa de "contraseña no usable" (usable_password/usable_password).
    Esto evita que alguien pueda deshabilitar su propia contraseña desde la UI.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # eliminar el campo toggle que permite marcar la contraseña como no usable
        self.fields.pop('usable_password', None)


# -----------------------
# Custom User admin
# -----------------------
User = get_user_model()

# Asegurarse de desregistrar el admin original antes de registrar el personalizado
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    change_password_form = SafeAdminPasswordChangeForm

    list_display = (
        'username', 'email', 'is_active',
        'is_staff', 'is_superuser', 'mostrar_grupos'
    )
    list_filter = ('groups', 'is_staff', 'is_superuser', 'is_active')
    actions = ('aprobar_usuarios', 'resetear_password')

    # Definir fieldsets explícitos para evitar referencias a campos que no existan
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Estado', {'fields': ('is_active', 'groups')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # -------------------
    # Helpers
    # -------------------
    def mostrar_grupos(self, obj):
        return ", ".join(g.name for g in obj.groups.all()) or "—"
    mostrar_grupos.short_description = "Grupos"

    # -------------------
    # Acciones de admin
    # -------------------
    def aprobar_usuarios(self, request, queryset):
        """Mover usuarios de 'Ingresantes' a 'Usuarios'."""
        g_ing, _ = Group.objects.get_or_create(name='Ingresantes')
        g_usr, _ = Group.objects.get_or_create(name='Usuarios')

        count = 0
        for u in queryset:
            u.groups.remove(g_ing)
            u.groups.add(g_usr)
            u.save()
            count += 1

        self.message_user(request, f"{count} usuario(s) aprobados.")
    aprobar_usuarios.short_description = "Aprobar usuarios"

    def resetear_password(self, request, queryset):
        """Resetear contraseñas. Si el actor no es superuser, no tocar staff ni superusers."""
        original_count = queryset.count()
        if not request.user.is_superuser:
            queryset = queryset.filter(is_staff=False, is_superuser=False)

        skipped = original_count - queryset.count()
        updated = 0

        for u in queryset:
            nueva = secrets.token_urlsafe(10)
            u.password = make_password(nueva)
            u.save()
            updated += 1
            # Recomendación: enviar por email en vez de mostrar en pantalla
            # send_mail('Tu nueva contraseña', f'Tu nueva contraseña: {nueva}', 'from@example.com', [u.email], fail_silently=True)

        msg = f"{updated} contraseña(s) reseteada(s)."
        if skipped:
            msg += f" Se omitieron {skipped} usuario(s) por permisos."
        self.message_user(request, msg)
    resetear_password.short_description = "Resetear contraseña"

    # -------------------
    # Seguridad en la UI
    # -------------------
    def get_readonly_fields(self, request, obj=None):
        # Si el usuario se edita a sí mismo, los grupos no deben ser editables
        if obj and obj == request.user:
            return ('groups',)
        return super().get_readonly_fields(request, obj)

    def get_fieldsets(self, request, obj=None):
        """Ajusta dinámicamente los fieldsets para ocultar campos sensibles
        cuando corresponda (p. ej. grupos cuando el usuario se edite a sí mismo).
        """
        fieldsets = super().get_fieldsets(request, obj)
        nuevos = []

        for name, opts in fieldsets:
            fields = list(opts.get('fields', ()))

            # Nunca incluir 'is_staff' ni 'is_superuser' en los fieldsets visibles
            for f in ('is_staff', 'is_superuser'):
                if f in fields:
                    fields.remove(f)

            # Si se edita a sí mismo, ocultar grupos
            if obj and obj == request.user and 'groups' in fields:
                fields.remove('groups')

            nuevos.append((name, {**opts, 'fields': tuple(fields)}))

        return tuple(nuevos)

    def get_form(self, request, obj=None, **kwargs):
        """Remueve campos peligrosos del formulario y evita KeyError con pop(..., None)."""
        form = super().get_form(request, obj, **kwargs)

        # Si no es superuser, no permitimos ver permisos individuales
        if not request.user.is_superuser:
            form.base_fields.pop('user_permissions', None)

        # Si el usuario se edita a sí mismo, ocultar groups en el form
        if obj and obj == request.user:
            form.base_fields.pop('groups', None)

        return form

    # -------------------
    # Seguridad en el backend
    # -------------------
    def save_model(self, request, obj, form, change):
        # Si el usuario se está editando a sí mismo, impedir cambios en grupos o permisos
        if change and obj == request.user:
            form.cleaned_data.pop('groups', None)
            form.cleaned_data.pop('user_permissions', None)
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        # Un staff normal no puede editar superusers
        if obj and getattr(obj, 'is_superuser', False) and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and getattr(obj, 'is_superuser', False) and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
