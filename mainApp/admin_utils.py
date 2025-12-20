from django.shortcuts import redirect
from django.contrib import messages


class DenyRedirectAdminMixin:
    """Mixin que redirige y muestra un mensaje en lugar de devolver 403 en el admin."""
    def _deny_and_redirect(self, request, message=None):
        messages.error(request, message or "No tienes permiso para realizar esta acción.")
        return redirect("/admin/")

    def add_view(self, request, form_url="", extra_context=None):
        if not self.has_add_permission(request):
            return self._deny_and_redirect(request)
        return super().add_view(request, form_url, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        # llamamos a has_delete_permission sin objeto por compatibilidad
        if not self.has_delete_permission(request):
            return self._deny_and_redirect(request)
        return super().delete_view(request, object_id, extra_context)
