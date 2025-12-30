from django.contrib.auth.forms import AdminPasswordChangeForm

class CustomAdminPasswordChangeForm(AdminPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Elimina la opción "Autenticación basada en contraseña"
        self.fields.pop("usable_password", None)
