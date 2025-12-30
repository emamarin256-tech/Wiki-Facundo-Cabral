from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group, Permission
from django.contrib.admin import SimpleListFilter
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import Rol, PerfilUsuario
from .admin_forms import CustomAdminPasswordChangeForm
from .admin_utils import DenyRedirectAdminMixin
User = get_user_model()


for model in (Group, Permission):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass



@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

    def has_module_permission(self, request):
        
        return request.user.is_superuser

    def get_model_perms(self, request):
        
        if request.user.is_superuser:
            return super().get_model_perms(request)
        return {}
    
    def _deny_and_redirect(self, request):
        messages.error(
            request,
            "No tienes permiso para acceder a esta sección."
        )
        return redirect("/admin/")

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            return self._deny_and_redirect(request)
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if not request.user.is_superuser:
            return self._deny_and_redirect(request)
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        if not request.user.is_superuser:
            return self._deny_and_redirect(request)
        return super().delete_view(request, object_id, extra_context)

class RolListFilter(SimpleListFilter):
    title = "Rol"
    parameter_name = "rol"

    def lookups(self, request, model_admin):
        return [
            (rol.pk, rol.nombre)
            for rol in Rol.objects.all()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(perfil__rol_id=self.value())
        return queryset


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    extra = 0
    fields = ("rol",)  

    def has_view_permission(self, request, obj=None):
        
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        
        return request.user.is_staff

    def has_add_permission(self, request, obj=None):
        
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        """
        Decidir cuándo el campo 'rol' es readonly:
        - Superuser: nada readonly.
        - Staff (no-superuser):
            * Si estoy editando mi propio usuario => rol readonly (no puedo cambiar mi rol).
            * Si el usuario objetivo es staff o superuser => rol readonly.
            * Si el usuario objetivo es Usuario o Ingresante => editable.
        - Si obj is None (creación) => readonly para staff (pero staff no puede añadir de todas formas).
        """
        if request.user.is_superuser:
            return ()

        
        if not request.user.is_staff:
            return ("rol",)

        
        if obj is None:
            return ("rol",)

        
        if getattr(obj, "pk", None) == getattr(request.user, "pk", None):
            return ("rol",)

        
        if getattr(obj, "is_staff", False) or getattr(obj, "is_superuser", False):
            return ("rol",)

        
        return ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Filtrar las opciones del dropdown 'rol' según quien edita:
        - Superuser: todas las opciones.
        - Staff: excluir el rol 'Staff' (no pueden asignar ese rol).
        - Otros: queryset vacío (no deberían ver el inline).
        """
        if db_field.name == "rol":
            if request.user.is_superuser:
                kwargs["queryset"] = Rol.objects.all()
            elif request.user.is_staff:
                
                kwargs["queryset"] = Rol.objects.exclude(nombre__in=["Staff"])
            else:
                kwargs["queryset"] = Rol.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class CustomUserAdmin(DenyRedirectAdminMixin, BaseUserAdmin):
    """
    Reglas principales:
    - Solo users con is_staff pueden entrar al admin (has_module_permission).
    - Superuser: puede todo.
    - Staff:
      * ven inline PerfilUsuario y pueden editar campos personales.
      * pueden editar rol de usuarios cuya rol ORIGINAL sea 'Usuario' o 'Ingresante' (no propio ni de otros staff/superusers).
      * no pueden crear/eliminar usuarios ni cambiar flags is_staff/is_superuser.
    """
    inlines = (PerfilUsuarioInline,)
    change_password_form = CustomAdminPasswordChangeForm
    filter_horizontal = ()

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información personal", {"fields": ("first_name", "last_name", "email")}),
        ("Estado", {"fields": ("is_active",)}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )


    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2"),
        }),
    )

    search_fields = ("username", "email")
    ordering = ("username",)

    
    def get_list_display(self, request):
        base = ("username", "email", "get_rol", "is_active")
        if request.user.is_superuser:
            return base + ("is_staff", "is_superuser")
        
        if request.user.is_staff:
            return base + ("is_superuser",)
        return base

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return (
                "is_active",
                "is_staff",
                "is_superuser",
                RolListFilter,
            )

        if request.user.is_staff:
            return (
                "is_active",
                "is_superuser",
                RolListFilter,
            )

        return ()


    def get_rol(self, obj):
        try:
            perfil = getattr(obj, "perfil", None)
            if not perfil:
                perfil = PerfilUsuario.objects.select_related("rol").filter(user=obj).first()
            if perfil and getattr(perfil, "rol", None):
                return perfil.rol.nombre
        except Exception:
            pass
        return "—"
    get_rol.short_description = "Rol"


    def has_module_permission(self, request):
        return request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff


    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        
        if request.user.is_superuser:
            return True

       
        if not request.user.is_staff:
            return False

        
        if obj is None:
            return True

        
        if obj.pk == request.user.pk:
            return True

        
        if getattr(obj, "is_staff", False) or getattr(obj, "is_superuser", False):
            return False

        
        return True


    def get_readonly_fields(self, request, obj=None):
        
        if obj and obj.pk == request.user.pk:
            return ("is_active",)

        
        if request.user.is_superuser:
            return ()

        
        return ("is_staff", "is_superuser", "is_active")




    def get_inline_instances(self, request, obj=None):
        inlines = []
        for inline in super().get_inline_instances(request, obj):
            if isinstance(inline, PerfilUsuarioInline):
                if request.user.is_staff:
                    inlines.append(inline)
            else:
                inlines.append(inline)
        return inlines
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_staff and not request.user.is_superuser:
            request.GET = request.GET.copy()
            for key in ("is_staff", "is_staff__exact"):
                request.GET.pop(key, None)

        return qs



    def changelist_view(self, request, extra_context=None):
        if request.user.is_staff and not request.user.is_superuser:
            forbidden = {"is_staff", "is_staff__exact"}

            if forbidden.intersection(request.GET):

                params = request.GET.copy()
                for f in forbidden:
                    params.pop(f, None)
                params["e"] = "1"

                return HttpResponseRedirect(
                    f"{request.path}?{params.urlencode()}"
                )

        return super().changelist_view(request, extra_context)


    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            original = User.objects.filter(pk=getattr(obj, "pk", None)).first()
            if original:
                obj.is_staff = original.is_staff
                obj.is_superuser = original.is_superuser
            else:
                obj.is_staff = False
                obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Protecciones adicionales en el inline PerfilUsuario:
        - Si el editor NO es superuser, restauramos el rol en casos prohibidos:
            * Si el usuario objetivo es staff o superuser -> no permitir cambio.
            * Si el usuario objetivo es el propio staff -> no permitir cambio.
          Si el objetivo es un usuario normal/ingresante, permitimos el cambio.
        """
        if formset.model is PerfilUsuario and not request.user.is_superuser:
            for f in formset.forms:
                if not hasattr(f, "instance") or not f.instance:
                    continue

                instance = f.instance
                if not getattr(instance, "pk", None):

                    try:
                        instance.rol_id = None
                    except Exception:
                        pass
                    continue


                orig_rol_id = PerfilUsuario.objects.filter(pk=instance.pk).values_list("rol_id", flat=True).first()
                target_user = None
                if getattr(instance, "user_id", None):
                    target_user = User.objects.filter(pk=instance.user_id).first()

                if target_user and target_user.pk == request.user.pk:
                    instance.rol_id = orig_rol_id
                    continue

                if target_user and (getattr(target_user, "is_staff", False) or getattr(target_user, "is_superuser", False)):
                    instance.rol_id = orig_rol_id
                    continue

                if instance.rol_id:
                    rol_nombre = Rol.objects.filter(pk=instance.rol_id).values_list("nombre", flat=True).first()
                    if rol_nombre == "Staff":
                        instance.rol_id = orig_rol_id

        return super().save_formset(request, form, formset, change)
