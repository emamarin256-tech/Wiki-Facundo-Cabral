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

    perfil, _ = PerfilUsuario.objects.get_or_create(user=instance)
    if perfil.rol != staff_rol:
        perfil.rol = staff_rol
        perfil.save(update_fields=['rol'])

    if not instance.is_staff:
        instance.is_staff = True
        instance.save(update_fields=['is_staff'])
