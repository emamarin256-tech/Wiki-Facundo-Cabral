# mainApp/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario, Rol

User = get_user_model()

@receiver(post_save, sender=PerfilUsuario)
def sync_is_staff_with_rol(sender, instance, created, **kwargs):
    """
    Si el perfil tiene rol 'Staff' -> user.is_staff = True.
    Si no tiene rol 'Staff' -> user.is_staff = False (salvo si es superuser).
    """
    user = instance.user
    try:
        staff_rol = Rol.objects.get(nombre='Staff')
    except Rol.DoesNotExist:
        return

    should_be_staff = (instance.rol == staff_rol)
    if should_be_staff and not user.is_staff:
        user.is_staff = True
        user.save(update_fields=['is_staff'])
    elif not should_be_staff and user.is_staff and not user.is_superuser:
        user.is_staff = False
        user.save(update_fields=['is_staff'])


@receiver(post_save, sender=User)
def assign_staff_role_to_superuser(sender, instance, created, **kwargs):
    """
    Si un usuario es superuser, asegurar que tenga el rol 'Staff' (crear perfil si hace falta).
    También dejamos is_staff en True (Django hace esto al crear superuser, pero lo reafirmamos).
    """
    if not instance.is_superuser:
        return

    try:
        staff_rol, _ = Rol.objects.get_or_create(nombre='Staff')
    except Exception:
        return

    perfil, _ = PerfilUsuario.objects.get_or_create(user=instance, defaults={'rol': staff_rol})
    if perfil.rol != staff_rol:
        perfil.rol = staff_rol
        perfil.save(update_fields=['rol'])

    if not instance.is_staff:
        instance.is_staff = True
        instance.save(update_fields=['is_staff'])


@receiver(post_save, sender=User)
def create_profile_on_user_create(sender, instance, created, **kwargs):
    """
    Si se crea un User, asegurar que exista un PerfilUsuario asociado.
    Asigna el rol por defecto 'Ingresante' si está disponible, sino usa el primer rol.
    """
    if not created:
        return

    try:
        # Intentar obtener rol por defecto 'Ingresante'
        try:
            default_rol = Rol.objects.get(nombre='Ingresante')
        except Rol.DoesNotExist:
            default_rol = Rol.objects.first()

        if default_rol is None:
            return

        PerfilUsuario.objects.get_or_create(user=instance, defaults={'rol': default_rol})
    except Exception:
        return
