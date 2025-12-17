from django.apps import AppConfig

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainApp'

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from django.db.utils import OperationalError, ProgrammingError
        from django.db.models.signals import pre_save, post_save, m2m_changed

        User = get_user_model()

        try:
            # Crear/obtener grupos base
            ingresante, _ = Group.objects.get_or_create(name='Ingresantes')
            usuario, _ = Group.objects.get_or_create(name='Usuarios')
            staff_group, _ = Group.objects.get_or_create(name='Staff')

            # Permisos para "Usuarios" (ejemplo: permisos de las apps listadas)
            perms_usuario = Permission.objects.filter(
                content_type__app_label__in=['blog', 'AppPagina', 'pagina', 'mainApp', 'layout']
            )
            usuario.permissions.set(perms_usuario)

            # Permisos sobre el modelo User para el grupo Staff
            ct_user = ContentType.objects.get_for_model(User)
            permisos_staff = Permission.objects.filter(
                content_type=ct_user,
                codename__in=['view_user', 'change_user', 'delete_user']
            )
            
            
            # Si querés reemplazar permisos existentes: use set(...)
            staff_group.permissions.set(permisos_staff)
            staff_group.permissions.add(*perms_usuario)

            # Señales para mantener coherencia is_staff <-> grupo Staff
            def user_pre_save(sender, instance, **kwargs):
                if getattr(instance, 'is_superuser', False):
                    instance.is_staff = True

            def user_post_save(sender, instance, created, **kwargs):
                staff, _ = Group.objects.get_or_create(name='Staff')
                if instance.is_superuser:
                    # Actualizamos directamente en DB para evitar loops
                    instance.__class__.objects.filter(pk=instance.pk).update(is_staff=True)
                    if not instance.groups.filter(pk=staff.pk).exists():
                        instance.groups.add(staff)
                    return

                if instance.groups.filter(pk=staff.pk).exists():
                    instance.__class__.objects.filter(pk=instance.pk).update(is_staff=True)
                else:
                    instance.__class__.objects.filter(pk=instance.pk).update(is_staff=False)

            pre_save.connect(user_pre_save, sender=User, dispatch_uid='mainapp_user_pre_save')
            post_save.connect(user_post_save, sender=User, dispatch_uid='mainapp_user_post_save')

            def user_groups_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
                if action in ('post_add', 'post_remove', 'post_clear'):
                    staff, _ = Group.objects.get_or_create(name='Staff')
                    if instance.groups.filter(pk=staff.pk).exists():
                        instance.__class__.objects.filter(pk=instance.pk).update(is_staff=True)
                    else:
                        if not getattr(instance, 'is_superuser', False):
                            instance.__class__.objects.filter(pk=instance.pk).update(is_staff=False)

            m2m_changed.connect(
                user_groups_changed,
                sender=User.groups.through,
                dispatch_uid='mainapp_user_groups_changed'
            )

        except (OperationalError, ProgrammingError):
            # tablas no disponibles todavía (migraciones iniciales)
            pass





