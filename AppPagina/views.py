from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404, redirect, render
from AppPagina.models import Pagina
from django.contrib import messages
import html

def cargar_url(request, slug):
    pagina = get_object_or_404(Pagina, slug=slug)
    texto = strip_tags(pagina.contenido or "")
    texto = html.unescape(texto).replace('\xa0', ' ').strip()
    if not texto:
        messages.error(request, f'La pagina "{pagina.titulo}" no tiene contenido cargado')
        return redirect("N_inicio")  # o raise Http404()
    return render(request, "paginas/pagina.html", {
        "v_titulo": pagina.titulo,
        "v_pag": pagina,
    })



        


def inicio(request):
    
    cargar_url_paginas = get_object_or_404(Pagina, es_inicio=True)
    return render(request,'paginas/pag_inicio.html',{
        'v_titulo':cargar_url_paginas.titulo,
        'v_pag': cargar_url_paginas,
        'v_pag_inicio': True}
        )