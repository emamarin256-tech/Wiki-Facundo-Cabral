from django import forms
from django.core import validators
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    last_name = forms.CharField(
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'autocomplete': 'off'})
    )
    email = forms.CharField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'autocomplete': 'off'})
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        validators=[
            validators.MinLengthValidator(
                8, message="La contraseña debe tener al menos 8 caracteres."
            )
        ],
    )

    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'})
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={'autocomplete': 'off'}),
        }
