from django.shortcuts import redirect, render
from django.contrib import messages
from AppPagina.models import Pagina
from .models import Categoria, Articulo, SubCategoria
import re
import html
from django.utils.html import strip_tags

# ------------------------------
# Listar artículos (pública)
# ------------------------------
def listar_articulos(request):
    # Sólo artículos públicos cuya categoría también sea pública
    lista = Articulo.objects.filter(publico=True, categoria__publico=True)
    return render(request, "articulos/articulos.html", {
        "titulo": "Artículos",
        "lista_art": lista
    })

def esta_vacio(html_text):
    if not html_text:
        return False
    # quitar etiquetas html
    text = strip_tags(html_text)
    # decodificar entidades como &nbsp;
    text = html.unescape(text)
    # convertir NBSP unicode a espacio y quitar espacios / caracteres invisibles
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
    # borrar cualquier whitespace y caracteres zero-width
    text = re.sub(r'[\s\u200B]+', '', text)
    return bool(text)


# ------------------------------
# Validación de subcategoría
# ------------------------------
def validacion_subcategoria(subcategoria, pagina):
    """
    Devuelve True si la subcategoría tiene contenido visible desde la página:
    - la subcategoria debe ser pública (y su categoría también, por las consultas)
    - o tener video/desc
    - o tener artículos públicos cuyo categoria sea pública y esté asociada a la página
    """
    if not getattr(subcategoria, "categoria", None) or not subcategoria.categoria.publico:
        return False    

    articulos = Articulo.objects.filter(
        subcategoria=subcategoria,
        tipo=pagina.tipo,
        publico=True,
        categoria__publico=True,
        categoria__paginas=pagina  # asegurar asociación categoría <-> página
    )
    return any([
        bool(subcategoria.publico),
        bool(subcategoria.video_file),
        bool(subcategoria.video_url),
        bool(subcategoria.desc),
        articulos.exists()
    ])


# ------------------------------
# Cargar página de categorías
# ------------------------------
def cargar_Pcategorias(request, Pagina_slug, Categoria_id):
    try:
        # Forzar que la página sea pública
        N_pagina = Pagina.objects.get(slug=Pagina_slug, publico=True)
    except Pagina.DoesNotExist:
        messages.error(request, "No se encontró esa página.")
        return redirect("N_inicio")

    try:
        # Forzar que la categoría sea pública y esté asociada a la página (ManyToMany)
        categoria = Categoria.objects.get(id=Categoria_id, publico=True)
    except Categoria.DoesNotExist:
        messages.error(request, "No se encontró esa categoría para la página indicada.")
        return redirect("N_inicio")

    # Sólo subcategorías públicas cuya categoría es la verificada
    sub_categoriaA = SubCategoria.objects.filter(categoria=categoria, publico=True)

    if sub_categoriaA.exists():
        # Filtramos por contenido válido (validacion_subcategoria ya comprueba articulos públicos y asociación con la página)
        sub_categoriaB = [sub for sub in sub_categoriaA if validacion_subcategoria(sub, N_pagina)]

        if not sub_categoriaB:
            messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
            if esta_vacio(N_pagina.contenido):
                return redirect("N_pagina", N_pagina.slug)
            return redirect("N_inicio")

        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_cat_pagina': N_pagina.titulo,
            'v_cat_subcategorias': sub_categoriaB,
        })

    # Cuando no hay subcategorías públicas: comprobar artículos públicos en la categoría
    # Aseguramos además que la categoría esté asociada a la página (ya lo hicimos arriba)
    v_cat_articulos_qs = Articulo.objects.filter(
        categoria=categoria,
        tipo=N_pagina.tipo,
        publico=True,
        categoria__publico=True,
        categoria__paginas=N_pagina  # redundante por 'categoria', pero clara la intención
    )

    if v_cat_articulos_qs.exists():
        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_cat_pagina': N_pagina.titulo,
            'v_cat_articulos': v_cat_articulos_qs,
        })

    else:
        messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
        if esta_vacio(N_pagina.contenido):
            return redirect("N_pagina", N_pagina.slug)
        return redirect("N_inicio")


# ------------------------------
# Cargar página de subcategorías
# ------------------------------
def cargar_Psubcategorias(request, Pagina_slug, SubCategoria_slug):
    try:
        # Forzar que la página sea pública
        pagina = Pagina.objects.get(slug=Pagina_slug, publico=True)
    except Pagina.DoesNotExist:
        messages.error(request, "No se encontró esa página.")
        return redirect("N_inicio")

    try:
        # Forzar que la subcategoría sea pública, que su categoría sea pública
        # y que esa categoría esté asociada a la página (evita accesos desde páginas no relacionadas)
        subcategoria = SubCategoria.objects.get(
            slug=SubCategoria_slug,
            publico=True,
            categoria__publico=True,
            categoria__paginas=pagina
        )
    except SubCategoria.DoesNotExist:
        messages.error(request, "No se encontró esa subcategoría para la página indicada.")
        return redirect("N_inicio")

    # Sólo artículos públicos cuya categoría esté asociada a la página (seguridad doble)
    articulos = Articulo.objects.filter(
        subcategoria=subcategoria,
        tipo=pagina.tipo,
        publico=True,
        categoria__publico=True,
        categoria__paginas=pagina
    )

    # Si no hay contenido visible en la subcategoría, respetar la lógica de redirección
    if not (subcategoria.publico or subcategoria.video_file or subcategoria.video_url or subcategoria.desc or articulos.exists()):
        messages.error(request, f"No se han cargado elementos en {subcategoria.nombre}")
        # Redirigir a la página si tiene contenido, o a inicio
        if esta_vacio(pagina.contenido):
            return redirect("N_pagina", pagina.slug)
        return redirect("N_inicio")

    return render(request, "subcategorias/subcategoria.html", {
        "v_subcategoria": subcategoria,
        "v_subcat_art": articulos,
        "v_subcat_pagina": pagina.titulo,
    })


# ------------------------------
# Cargar detalle de artículo
# ------------------------------
def cargar_Darticulo(request, Pagina_slug, Articulo_id):
    try:
        # Forzar que la página sea pública
        pagina = Pagina.objects.get(slug=Pagina_slug, publico=True)
    except Pagina.DoesNotExist:
        messages.error(request, "No se encontró esa página.")
        return redirect("N_inicio")

    try:
        # Forzar que el artículo sea público, que su categoría sea pública,
        # y que esa categoría esté asociada a la página (impide acceso desde páginas no relacionadas)
        articulo = Articulo.objects.get(
            id=Articulo_id,
            tipo=pagina.tipo,
            publico=True,
            categoria__publico=True,
            categoria__paginas=pagina
        )
    except Articulo.DoesNotExist:
        messages.error(request, "No se encontró ese artículo para la página indicada.")
        return redirect("N_inicio")

    # Si el artículo tiene subcategoría, podemos añadir una comprobación adicional opcional:
    # si articulo.subcategoria and not articulo.subcategoria.publico: considerar bloquearlo.
    if getattr(articulo, 'subcategoria', None) and not articulo.subcategoria.publico:
        messages.error(request, "El artículo no esta disponible.")
        return redirect("N_inicio")

    return render(request, 'articulo/articulo_detalle.html', {
        'v_articulo': articulo,
    })
