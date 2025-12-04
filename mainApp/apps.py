from django.apps import AppConfig

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainApp'

    def ready(self):
        from django.contrib.auth.models import Group, Permission
        from django.db.utils import OperationalError, ProgrammingError

        try:
            # Crear grupos base
            ingresante, _ = Group.objects.get_or_create(name='Ingresantes')
            usuario, _ = Group.objects.get_or_create(name='Usuarios')
            staff, _ = Group.objects.get_or_create(name='Staff')

            # Obtener todos los permisos
            permisos_usuario = Permission.objects.filter(content_type__app_label__in=['blog', 'AppPagina','pagina','mainApp','layout',])

            # Asignar los permisos al grupo "Usuarios"
            usuario.permissions.set(permisos_usuario)

        except (OperationalError, ProgrammingError):
            # ocurre si las tablas todavía no existen (ej: primera migración)
            pass




