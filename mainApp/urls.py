from django.urls import path
from . import views

urlpatterns= [
    path("registro/",views.f_registro,name="N_registro"),
    path("sesion/", views.f_inicio_sesion, name="N_inicio_sesion"),
    path("cerrar-sesion/",views.f_cerrar_sesion,name="N_cerrar_sesion"),
    path("usuario/",views.f_usuario, name="N_usuario"),
    ]
