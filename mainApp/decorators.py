# ...existing code...
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def group_required(group_name):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Si no está autenticado, añadimos mensaje y redirigimos al login (con next)
            if not request.user.is_authenticated:
                messages.info(request, "Debes iniciar sesión para acceder a esta sección.")
                login_url = reverse("N_inicio_sesion")
                return redirect(f"{login_url}?next={request.get_full_path()}")

            # Si está autenticado y pertenece al grupo (o es superuser), permitimos acceso
            if request.user.groups.filter(name=group_name).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Si está autenticado pero no tiene permiso, mensaje y redirección a inicio
            messages.warning(request, "No tienes permiso para acceder a esta sección.")
            return redirect("N_inicio")
        return _wrapped_view
    return decorator
