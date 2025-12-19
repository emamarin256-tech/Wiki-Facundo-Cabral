# mainApp/apps.py 
from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainApp'
    verbose_name = 'Autenticación y Autorización'
    
    def ready(self):
        from .models import Rol
        try:
            Rol.objects.get_or_create(nombre='Ingresante')
            Rol.objects.get_or_create(nombre='Usuario')
            Rol.objects.get_or_create(nombre='Staff')
        except (OperationalError, ProgrammingError):
            # Las tablas aún no existen (migraciones)
            pass

        # IMPORTANTE: registrar las señales
        try:
            from . import signals  # carga el archivo signals.py y conecta los receivers
        except Exception:
            # evitar fallos en migraciones o entornos incompletos
            pass





