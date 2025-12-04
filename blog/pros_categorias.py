from .models import Categoria

def C_obtener_paginas(request):
    categorias = Categoria.objects.filter(publico=True).values_list(
    'id', 'nombre', 'paginas__titulo')

    

    return{
        'V_categorias':categorias,
    }