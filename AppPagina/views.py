from django.shortcuts import get_object_or_404, redirect, render
from AppPagina.models import Pagina
from django.contrib import messages
# Create your views here.

def cargar_url(request,slug):
    
    cargar_url_paginas = get_object_or_404(Pagina, slug=slug)
    if cargar_url_paginas.contenido =="":
        messages.error(request, f'La pagina "{cargar_url_paginas.titulo}" no tiene contenido cargado')
        return redirect("N_inicio")
    else:
        return render(request,'paginas/pagina.html',{
            'titulo':cargar_url_paginas.titulo,
            'pag': cargar_url_paginas})
        


def inicio(request):
    
    cargar_url_paginas = get_object_or_404(Pagina, es_inicio=True)
    return render(request,'paginas/pag_inicio.html',{
        'titulo':cargar_url_paginas.titulo,
        'pag': cargar_url_paginas,
        'pag_inicio': True}
        )