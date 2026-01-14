from django.utils.html import strip_tags
import html
from AppPagina.models import Pagina

def obtener_paginas(request):
    qs = Pagina.objects.filter(publico=True).order_by('orden').values_list(
        'id','titulo','slug','tipo__nombre','contenido'
    )
    paginas = []
    for id_, titulo, slug, tipo_nombre, contenido in qs:
        texto = strip_tags(contenido or "")
        texto = html.unescape(texto).replace('\xa0', ' ').strip()
        paginas.append((id_, titulo, slug, tipo_nombre, texto))
    return {'V_paginas': paginas}
