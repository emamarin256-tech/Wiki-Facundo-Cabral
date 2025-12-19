from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def rol_required(*roles_permitidos):
    """
    Permite acceso si:
    - es superusuario
    - su rol está dentro de roles_permitidos
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            # No autenticado → login con next
            if not request.user.is_authenticated:
                messages.info(
                    request,
                    "Debes iniciar sesión para acceder a esta sección."
                )
                login_url = reverse("N_inicio_sesion")
                return redirect(f"{login_url}?next={request.get_full_path()}")

            # Superusuario siempre pasa
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Usuario sin perfil o sin rol
            perfil = getattr(request.user, 'perfil', None)
            if not perfil or not perfil.rol:
                messages.warning(
                    request,
                    "Espera a ser aceptado para acceder al mantenimiento del sitio."
                )
                return redirect("N_inicio")

            # Rol permitido (OR lógico, igual que __in)
            if perfil.rol.nombre in roles_permitidos:
                return view_func(request, *args, **kwargs)

            # Autenticado pero sin permiso
            messages.warning(
                request,
                "No tienes permiso para acceder a esta sección."
            )
            return redirect("N_inicio")

        return _wrapped_view
    return decorator


