from django.urls import path
from . import views

urlpatterns = [
    path('mantenimiento/crear/<str:modelo>', views.crear, name="N_crear"),
    path('mantenimiento/<str:modelo>/<int:pk>', views.f_mantenimientoC, name="N_mantenimientoC"),
    path('mantenimiento/',views.f_mantenimiento, name='N_mantenimiento'),
    path('mantenimiento/<str:modelo>', views.f_mantenimientoB, name="N_mantenimientoB"),
    path('mantenimiento/eliminar_varios/<str:modelo>', views.eliminar_varios, name="N_eliminar_varios"),

]
