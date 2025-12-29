from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import UserCreationForm
from mainApp.forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Rol, PerfilUsuario
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

# =============================
# VISTAS PRINCIPALES
# =============================
from django.shortcuts import render

def mi_error_404(request, exception):
    return render(request, 'temp_mainApp/404.html', status=404)




def f_usuario(request):
        if not request.user.is_authenticated:
            messages.info(request, "Debes iniciar sesión para acceder a esta sección.")
            login_url = reverse("N_inicio_sesion")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        else:
            return render(request, "temp_mainApp/usuario.html")


# =============================
# REGISTRO DE USUARIO
# =============================

def f_registro(request):
    # Si ya está logueado, redirige al inicio de sesión
    if request.user.is_authenticated:
        return redirect("N_inicio_sesion")

    reg = RegisterForm()

    if request.method == "POST":
        reg = RegisterForm(request.POST)
        if reg.is_valid():
            user = reg.save()

            rol_ingresante = Rol.objects.get(nombre='Ingresante')
            PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={'rol': rol_ingresante}
            )


            messages.success(
                request,
                
                "Ya podés iniciar sesión como Ingresante. "
                "Un miembro del staff deberá aprobar tu cuenta antes de poder acceder al mantenimiento del sitio"
            )
            return redirect("N_inicio_sesion")

    return render(request, "usuarios/registro.html", {
        "titulo": "registro",
        "register_form": reg
    })


# =============================
# INICIO DE SESIÓN
# =============================

@never_cache
def f_inicio_sesion(request):
    if request.user.is_authenticated:
        return redirect("N_usuario")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "¡Iniciaste sesión correctamente!")
            return redirect("N_usuario")
        else:
            messages.warning(request, "No se encontró el usuario o la contraseña es incorrecta.")
            return redirect("N_inicio_sesion")

    return render(request, "usuarios/inicio_sesion.html", {
        "titulo": "Identificate"
    })


# =============================
# CERRAR SESIÓN
# =============================

def f_cerrar_sesion(request):
    logout(request)
    messages.success(request, "Cerraste sesión!")
    return redirect("N_inicio_sesion")
