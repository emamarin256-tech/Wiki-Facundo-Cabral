from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponseRedirect
from AppPagina.models import Pagina
from .models import Categoria, Articulo, SubCategoria


# ------------------------------
# Listar artículos
# ------------------------------
def listar_articulos(request):
    lista = Articulo.objects.all()
    return render(request, "articulos/articulos.html", {
        "titulo": "Artículos",
        "lista_art": lista
    })


# ------------------------------
# Validación de subcategoría
# ------------------------------
def validacion_subcategoria(subcategoria, pagina):
    articulos = Articulo.objects.filter(subcategoria=subcategoria, tipo=pagina.tipo, publico=True)
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
        N_pagina = Pagina.objects.get(slug=Pagina_slug)
        categoria = Categoria.objects.get(id=Categoria_id)
    except (Pagina.DoesNotExist, Categoria.DoesNotExist):
        messages.error(request, "No se encontro esa página.")
        return redirect("N_inicio")

    sub_categoriaA = SubCategoria.objects.filter(categoria__id=Categoria_id, publico=True)

    if sub_categoriaA.exists():
        sub_categoriaB = [sub for sub in sub_categoriaA if validacion_subcategoria(sub, N_pagina)]

        if not sub_categoriaB:
            if N_pagina.contenido:
                messages.error(request, f"No se han cargado elementos en {categoria.nombre}")             
                return redirect("N_pagina", N_pagina.slug)
            else:
                messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
                return redirect("N_inicio")

        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_cat_pagina': N_pagina.titulo,
            'v_cat_subcategorias': sub_categoriaB,
        })

    elif Articulo.objects.filter(categoria__id=Categoria_id, tipo=N_pagina.tipo).exists():
        v_cat_articulos = Articulo.objects.filter(categoria__id=Categoria_id, tipo=N_pagina.tipo, publico=True)
        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_cat_pagina': N_pagina.titulo,
            'v_cat_articulos': v_cat_articulos,
        })

    else:
        messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
        if N_pagina.contenido:
            return redirect("N_pagina", N_pagina.slug)
        return redirect("N_inicio")


# ------------------------------
# Cargar página de subcategorías
# ------------------------------
def cargar_Psubcategorias(request, Pagina_slug, SubCategoria_slug):
    try:
        pagina = Pagina.objects.get(slug=Pagina_slug)
        subcategoria = SubCategoria.objects.get(slug=SubCategoria_slug)
    except (Pagina.DoesNotExist, SubCategoria.DoesNotExist):
        messages.error(request, "No se encontro esa página.")
        return redirect("N_inicio")

    articulos = Articulo.objects.filter(subcategoria__slug=SubCategoria_slug, tipo=pagina.tipo, publico=True)

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
        pagina = Pagina.objects.get(slug=Pagina_slug)
        articulo = Articulo.objects.get(id=Articulo_id, tipo=pagina.tipo)
    except (Pagina.DoesNotExist, Articulo.DoesNotExist):
        messages.error(request, "No se encontro esa página.")
        return redirect("N_inicio")

    return render(request, 'articulo/articulo_detalle.html', {
        'v_articulo': articulo,
    })
