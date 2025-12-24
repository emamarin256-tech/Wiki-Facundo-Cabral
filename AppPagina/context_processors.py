from .models import Pagina

def obtener_paginas(request):
    paginas = Pagina.objects.filter(publico=True).order_by('orden').values_list('id','titulo','slug','tipo__nombre','contenido')
    
    return{
        'V_paginas':paginas
    }