# mainApp/management/commands/seed.py
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction

from mainApp.models import Rol, PerfilUsuario

DEFAULT_PASSWORD = os.environ.get("DJANGO_SEED_DEFAULT_PASSWORD", "test1234")

class Command(BaseCommand):
    help = (
        "Crea usuarios y perfiles de prueba: Dueño (superuser), colaborador1, colaborador2. "
        "Opcionalmente carga fixtures de blog y AppPagina."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--load-fixtures',
            action='store_true',
            help='Cargar fixtures después de crear usuarios.'
        )
        parser.add_argument(
            '--fixture-list',
            nargs='*',
            help='Lista de fixtures a cargar (por ejemplo: blog/fixtures/blog_data.json AppPagina/fixtures/AppPagina_data.json).'
        )
        parser.add_argument(
            '--password',
            type=str,
            help=f'Establecer contraseña por defecto para nuevos usuarios (por defecto: env DJANGO_SEED_DEFAULT_PASSWORD o "{DEFAULT_PASSWORD}").'
        )
        parser.add_argument(
            '--force-password',
            action='store_true',
            help='Si se pasa, FORZAR la contraseña para usuarios ya existentes también (usar con cuidado).'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        pwd = options.get('password') or DEFAULT_PASSWORD
        force_pwd = bool(options.get('force_password'))

        # 1) Asegurar roles básicos (aunque los crea AppConfig.ready, es seguro reafirmarlo)
        roles = {}
        for rname in ("Ingresante", "Usuario", "Staff"):
            rol_obj, _ = Rol.objects.get_or_create(nombre=rname)
            roles[rname] = rol_obj
        self.stdout.write(self.style.SUCCESS("Roles asegurados: Ingresante, Usuario, Staff"))

        # 2) Crear usuarios colaboradores (usuarios normales) y asignar rol 'Usuario'
        for username in ("colaborador1", "colaborador2"):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                }
            )
            if created:
                user.set_password(pwd)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario {username} creado (password por defecto)."))
            else:
                if force_pwd:
                    user.set_password(pwd)
                    user.save()
                    self.stdout.write(self.style.WARNING(f"Usuario {username} existía — contraseña FORZADA."))
                else:
                    self.stdout.write(f"Usuario {username} ya existe — contraseña no modificada.")

            perfil, pcreated = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={"rol": roles["Usuario"]}
            )
            if not pcreated and perfil.rol != roles["Usuario"]:
                perfil.rol = roles["Usuario"]
                perfil.save()
                self.stdout.write(f"Perfil de {username} actualizado a rol 'Usuario'.")
            else:
                self.stdout.write(f"Perfil de {username} asegurado con rol 'Usuario'.")

        # 3) Crear/asegurar Dueño como superuser y asignar rol 'Staff'
        owner_username = "Dueño"
        owner_defaults = {
            "email": "dueno@example.com",
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        }
        owner_user, owner_created = User.objects.get_or_create(
            username=owner_username,
            defaults=owner_defaults
        )

        if owner_created:
            owner_user.set_password(pwd)
            owner_user.is_staff = True
            owner_user.is_superuser = True
            owner_user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser {owner_username} creado (password por defecto)."))
        else:
            changed = False
            if not owner_user.is_staff:
                owner_user.is_staff = True
                changed = True
            if not owner_user.is_superuser:
                owner_user.is_superuser = True
                changed = True
            if changed:
                owner_user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario {owner_username} actualizado a superuser/is_staff."))
            else:
                self.stdout.write(f"Usuario {owner_username} ya existe y ya es superuser/is_staff.")
            if force_pwd:
                owner_user.set_password(pwd)
                owner_user.save()
                self.stdout.write(self.style.WARNING(f"Contraseña de {owner_username} FORZADA."))

        perfil_owner, pcreated_owner = PerfilUsuario.objects.get_or_create(
            user=owner_user,
            defaults={"rol": roles["Staff"]}
        )
        if not pcreated_owner and perfil_owner.rol != roles["Staff"]:
            perfil_owner.rol = roles["Staff"]
            perfil_owner.save()
            self.stdout.write(f"Perfil de {owner_username} actualizado a rol 'Staff'.")
        else:
            self.stdout.write(f"Perfil de {owner_username} asegurado con rol 'Staff'.")

        # 4) Opcional: cargar fixtures
        if options.get("load_fixtures"):
            fixtures = options.get("fixture_list") or [
                "blog/fixtures/blog_data.json",
                "AppPagina/fixtures/AppPagina_data.json",
            ]
            for fx in fixtures:
                try:
                    call_command("loaddata", fx)
                    self.stdout.write(self.style.SUCCESS(f"Fixture cargada: {fx}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error cargando fixture {fx}: {e}"))

        self.stdout.write(self.style.SUCCESS("Seed finalizado."))
