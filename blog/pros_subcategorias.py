from .models import SubCategoria

def SC_obtener_paginas(request):
    subcategorias = SubCategoria.objects.filter(publico=True).values_list(
    'id', 'nombre','slug',)

    

    return{
        'V_subcategorias':subcategorias,
    }