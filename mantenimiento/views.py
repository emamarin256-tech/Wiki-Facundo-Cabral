from django.db.models import Q
from django.apps import apps
from django.forms import modelform_factory
from ckeditor.widgets import CKEditorWidget
from django.views.decorators.cache import never_cache
from django.shortcuts import render, get_object_or_404, redirect
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import models
from django.contrib import messages
from mainApp.models import Layout
from mainApp.decorators import group_required


# ==========================
# FUNCIONES AUXILIARES
# ==========================

def conseguir_modelos(modelo):
    apps_a_buscar = ["blog", "AppPagina", "mainApp"]
    for app_label in apps_a_buscar:
        try:
            return apps.get_model(app_label, modelo)
        except LookupError:
            continue
    return None


def lista_Modelos():
    lista = []
    for app_label in ["AppPagina", "blog", "mainApp"]:
        app_config = apps.get_app_config(app_label)
        lista.extend(app_config.get_models())
    return lista


def crear_formulario_con_widgets(Modelo):
    from django_select2.forms import Select2MultipleWidget
    widgets = {}
    for field in Modelo._meta.get_fields():
        if isinstance(field, models.TextField):
            widgets[field.name] = CKEditorWidget()
        elif isinstance(field, models.ManyToManyField):
            widgets[field.name] = Select2MultipleWidget()
    return modelform_factory(Modelo, fields="__all__", widgets=widgets)


# ==========================
# VISTAS
# ==========================

@group_required("Usuarios", "Staff")
def f_mantenimiento(request):
    try:
        Lista_modelos = lista_Modelos()
        lista_modelos = []
        lay = None

        for modelo in Lista_modelos:
            if modelo.__name__ == "Layout":
                lay = Layout.get_solo()
            else:
                lista_modelos.append(modelo.__name__)

        response = render(request, "mantenimiento/mantenimiento.html", {
            "lista_modelos": lista_modelos,
            "layo": lay
        })
        storage = messages.get_messages(request)
        storage.used = True
        return response

    except Exception as e:
        messages.error(request, "Ocurrió un error al cargar el mantenimiento.")
        return redirect("N_inicio")


@group_required("Usuarios", "Staff")
def f_mantenimientoB(request, modelo):
    Modelo = conseguir_modelos(modelo)
    if Modelo is None:
        messages.error(request, f"El modelo '{modelo}' no existe.")
        return redirect("N_mantenimiento")

    try:
        if modelo == "Layout":
            return redirect("N_mantenimiento")

        # Parámetros GET
        search_query = request.GET.get("q", "").strip()
        sort_field_raw = request.GET.get("sort", "").strip()
        sort_order = request.GET.get("order", "asc").strip().lower()

        # Queryset base
        instancias = Modelo.objects.all()

        # FILTRO DE BÚSQUEDA: solo 'nombre' o 'titulo' si existen
        if search_query:
            filtro_q = Q()
            posibles_campos = ["nombre", "titulo"]
            for campo in posibles_campos:
                if campo in [f.name for f in Modelo._meta.get_fields()]:
                    filtro_q |= Q(**{f"{campo}__istartswith": search_query})
            if filtro_q.children:
                instancias = instancias.filter(filtro_q)

        # --- Construir allowed_fields SIEMPRE con el fallback solicitado ---
        allowed_fields = []
        for campo in Modelo._meta.fields:
            tipo = campo.get_internal_type()
            if tipo == "CharField":
                # Sólo incluir 'nombre' o 'titulo' entre los CharField
                if campo.name in ("nombre", "titulo"):
                    allowed_fields.append(campo.name)
            elif tipo in (
                "DateField", "DateTimeField",
                "IntegerField", "FloatField",
                "BooleanField","ForeignKey"
            ):
                allowed_fields.append(campo.name)

        # Validar sort_order
        if sort_order not in ("asc", "desc"):
            if request.GET.get("order") not in (None, ""):
                messages.warning(request, f"Orden '{request.GET.get('order')}' no válido. Usando 'asc' por defecto.")
            sort_order = "asc"

        # Validar y aplicar sort_field
        campo_mostrado = None
        if sort_field_raw:
            if sort_field_raw not in allowed_fields:
                messages.warning(request, f"El campo '{sort_field_raw}' no es válido para ordenar. Se ignorará el orden.")
                sort_field_raw = ""
            else:
                campo_para_ordenar = f"-{sort_field_raw}" if sort_order == "desc" else sort_field_raw
                instancias = instancias.order_by(campo_para_ordenar)
                campo_mostrado = sort_field_raw

        # Obtener verbose_name del campo_mostrado (si aplica)
        campo_mostrado_verbose = None
        if campo_mostrado:
            for campo in Modelo._meta.fields:
                if campo.name == campo_mostrado:
                    campo_mostrado_verbose = campo.verbose_name
                    break

        # Preparar 'campos' para el template
        campos_para_template = []
        mapa_verbose = {f.name: f.verbose_name for f in Modelo._meta.fields}
        for nombre in allowed_fields:
            campos_para_template.append({
                "name": nombre,
                "verbose": mapa_verbose.get(nombre, nombre.replace("_", " ").capitalize())
            })

        return render(request, "mantenimiento/mantenimientoB.html", {
            "instancias": instancias,
            "modelo": modelo,
            "search_query": search_query,
            "sort_field": sort_field_raw,
            "sort_order": sort_order,
            "campo_mostrado": campo_mostrado,
            "campo_mostrado_verbose": campo_mostrado_verbose,
            "campos": campos_para_template,
        })

    except Exception as e:
        messages.error(request, f"Ocurrió un error al cargar los datos de {modelo}. ({e})")
        return redirect("N_mantenimiento")



@never_cache
@group_required("Usuarios", "Staff")
def f_mantenimientoC(request, modelo, pk):
    Modelo = conseguir_modelos(modelo)
    if Modelo is None:
        messages.error(request, f"El modelo '{modelo}' no existe.")
        return redirect("N_mantenimiento")

    try:
        instancia = get_object_or_404(Modelo, pk=pk)
    except Exception:
        messages.error(
            request, f"No se encontró la instancia seleccionada de {modelo}.")
        return redirect("N_mantenimientoB", modelo=modelo)

    Lista_modelos = lista_Modelos()
    lista_modelos = [{"name": m.__name__} for m in Lista_modelos]

    # widgets dinámicos
    widgets = {}
    for field in Modelo._meta.get_fields():
        if isinstance(field, models.TextField):
            widgets[field.name] = CKEditorWidget()

    Formulario = modelform_factory(Modelo, fields="__all__", widgets=widgets)

    try:
        if request.method == "POST":
            if request.POST.get("accion") == "eliminar":
                instancia.delete()
                messages.success(
                    request, f"Se eliminó correctamente {str(instancia)}.")
                return redirect("N_mantenimientoB", modelo=modelo)

            form = Formulario(request.POST, request.FILES, instance=instancia)

            if form.is_valid():
                instancia_guardada = form.save(commit=False)

                # Mantiene o asigna el usuario
                if hasattr(instancia_guardada, 'usuario'):
                    instancia_guardada.usuario = getattr(
                        instancia, 'usuario', request.user)

                instancia_guardada.save()
                form.save_m2m()

                if request.POST.get("accion") == "guardar":
                    messages.success(
                        request, f"Se guardó correctamente {str(instancia)}.")
                    return redirect("N_mantenimientoB", modelo=modelo)

                elif request.POST.get("accion") == "guardaryseguir":
                    messages.success(
                        request, f"Se guardó correctamente {str(instancia)}.")
                    return redirect("N_mantenimientoC", modelo=modelo, pk=pk)

            else:
                messages.warning(
                    request, "Por favor revisa los datos ingresados.")
        else:
            form = Formulario(instance=instancia)
            # Mostrar el usuario actual si el modelo lo tiene
            if hasattr(Modelo, 'usuario') or 'usuario' in [f.name for f in Modelo._meta.get_fields()]:
                form.fields['usuario'] = forms.CharField(
                    label="Usuario",
                    required=False,
                    disabled=True,
                    initial=getattr(instancia.usuario, 'username', '') if hasattr(
                        instancia, 'usuario') else ''
                )

        template = "mantenimiento/mantenimientoC_layout.html" if modelo == "Layout" else "mantenimiento/mantenimientoC.html"
        return render(request, template, {
            "form": form,
            "modelo": Modelo.__name__,
            "instancia": instancia,
            "lista_m": lista_modelos,
        })

    except Exception as e:
        messages.error(
            request, f"Ocurrió un error al procesar la edición de {modelo}.")
        raise
        return redirect("N_mantenimientoB", modelo=modelo)


@never_cache
@group_required("Usuarios", "Staff")
def crear(request, modelo):
    if str(modelo) == "Layout":
        return redirect("N_mantenimiento")

    Modelo = conseguir_modelos(modelo)
    if Modelo is None:
        messages.error(request, "El modelo especificado no existe.")
        return redirect("N_mantenimiento")

    try:
        Formulario = modelform_factory(Modelo, fields="__all__")

        if request.method == 'POST':
            form = Formulario(request.POST, request.FILES)
            if form.is_valid():
                instancia = form.save(commit=False)
                
                # Asegurarse de asignar usuario
                if 'usuario' in [f.name for f in Modelo._meta.fields]:
                    instancia.usuario = request.user
                
                instancia.save()
                form.save_m2m()


                accion = request.POST.get('accion')
                if accion == 'guardar':
                    messages.success(
                        request, f"Se guardó correctamente {Modelo.__name__}.")
                    return redirect('N_mantenimientoB', modelo=modelo)
                elif accion == 'guardaryseguir':
                    messages.success(
                        request, f"Se guardó correctamente {Modelo.__name__}. ¡Continúa editando!")
                    return redirect('N_crear', modelo=modelo)
            else:
                messages.warning(
                    request, "Por favor revisa los datos ingresados.")
        else:
            form = Formulario()

        descripcion_modelo = getattr(Modelo, 'descripcion_modelo', None)
        return render(request, 'mantenimiento/crear.html', {
            'Modelo': modelo,
            'form': form,
            'descripcion_modelo': descripcion_modelo,
        })

    except Exception as e:
        messages.error(
            request, f"Ocurrió un error al crear un nuevo {modelo}.")
        raise
        return redirect("N_mantenimiento")


@never_cache
@group_required("Usuarios", "Staff")
def eliminar_varios(request, modelo):
    Modelo = conseguir_modelos(modelo)
    if Modelo is None:
        messages.error(request, "Modelo no encontrado.")
        return redirect("N_mantenimiento")

    try:
        if request.method == "POST":
            ids = request.POST.getlist("seleccionados")
            if ids:
                eliminados = Modelo.objects.filter(pk__in=ids)
                cantidad = eliminados.count()
                eliminados.delete()
                messages.success(
                    request, f"Se eliminaron {cantidad} {modelo}(s) correctamente.")
            else:
                messages.warning(
                    request, "No seleccionaste ningún elemento para eliminar.")
    except Exception as e:
        messages.error(
            request, f"Ocurrió un error al eliminar los elementos de {modelo}.")

    return redirect("N_mantenimientoB", modelo=modelo)
