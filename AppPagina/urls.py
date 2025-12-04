from django.urls import path
from . import views

urlpatterns = [
path('<str:slug>/',views.cargar_url, name="N_pagina"),    
path('',views.inicio, name="N_inicio"),  
]

