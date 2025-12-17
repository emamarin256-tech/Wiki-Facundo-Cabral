from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def group_required(*group_names):

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

            # Autenticado y con grupo válido o superusuario
            if (
                request.user.is_superuser or
                request.user.groups.filter(name__in=group_names).exists()
            ):
                return view_func(request, *args, **kwargs)

            # Autenticado pero sin permiso
            messages.warning(
                request,
                "No tienes permiso para acceder a esta sección."
            )
            return redirect("N_inicio")

        return _wrapped_view
    return decorator

