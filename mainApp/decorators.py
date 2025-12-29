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

            
            if not request.user.is_authenticated:
                messages.info(
                    request,
                    "Debes iniciar sesión para acceder a esta sección."
                )
                login_url = reverse("N_inicio_sesion")
                return redirect(f"{login_url}?next={request.get_full_path()}")

            
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            
            perfil = getattr(request.user, 'perfil', None)
            if not perfil or not perfil.rol:
                messages.warning(
                    request,
                    "Espera a ser aceptado para acceder al mantenimiento del sitio."
                )
                return redirect("N_inicio")

            
            if perfil.rol.nombre in roles_permitidos:
                return view_func(request, *args, **kwargs)

            
            messages.warning(
                request,
                "No tienes permiso para acceder a esta sección."
            )
            return redirect("N_inicio")

        return _wrapped_view
    return decorator


