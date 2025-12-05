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
    articulos = Articulo.objects.filter(subcategoria__nombre=subcategoria, tipo=pagina.tipo, publico=True)
    return any([
        subcategoria.publico,  
        subcategoria.video_file,
        subcategoria.video_url,
        subcategoria.desc,
        articulos.exists()
    ])


# ------------------------------
# Cargar página de categorías
# ------------------------------
def cargar_Pcategorias(request, Pagina_slug, Categoria_id):
    try:
        pagina_n = Pagina.objects.get(slug=Pagina_slug)
        categoria = Categoria.objects.get(id=Categoria_id)
    except (Pagina.DoesNotExist, Categoria.DoesNotExist):
        messages.error(request, "No se encontro esa página.")
        return redirect("N_inicio")

    sub_categoriaA = SubCategoria.objects.filter(categoria__id=Categoria_id, publico=True)

    if sub_categoriaA.exists():
        sub_categoriaB = [sub for sub in sub_categoriaA if validacion_subcategoria(sub, pagina_n)]

        if not sub_categoriaB:
            if pagina_n.contenido:
                return redirect("N_pagina", pagina_n.slug)
            else:
                messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
                return redirect("N_inicio")

        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_pagina': pagina_n.titulo,
            'v_subcategorias': sub_categoriaB,
        })

    elif Articulo.objects.filter(categoria__id=Categoria_id, tipo=pagina_n.tipo).exists():
        vb_articulos = Articulo.objects.filter(categoria__id=Categoria_id, tipo=pagina_n.tipo, publico=True)
        return render(request, 'categorias/categoria.html', {
            'v_categoria': categoria,
            'v_pagina': pagina_n.titulo,
            'vb_articulos': vb_articulos,
        })

    else:
        messages.error(request, f"No se han cargado elementos en {categoria.nombre}")
        if pagina_n.contenido:
            return redirect("N_pagina", pagina_n.slug)
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
        "v_subcategoriaaa": subcategoria,
        "v_sart": articulos,
        "v_Pagina_Nombre": pagina.titulo,
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
