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
from blog.models import Layout
from mainApp.decorators import rol_required


# ==========================
# FUNCIONES AUXILIARES
# ==========================



def lista_Modelos():
    lista = []
    for app_label in ["AppPagina", "blog",]:
        app_config = apps.get_app_config(app_label)
        lista.extend(app_config.get_models())
    return lista


# ==========================
# VISTAS
# ==========================
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import DatabaseError

from mantenimiento import services, constants
from blog.models import Layout  # si lo necesitás solo para get_solo, lo resolvemos con services

logger = logging.getLogger(__name__)

@rol_required("Usuario", "Staff")
def f_mantenimiento(request):
    try:
        modelos = services.list_models()
        lista_modelos = []
        lay = None

        # Intentar obtener Layout de forma segura
        try:
            LayoutModel = services.get_model_by_name("Layout")
            # Llamada a get_solo puede provocar DatabaseError si no hay DB lista
            try:
                lay = LayoutModel.get_solo()
            except AttributeError:
                # Modelo no es Singleton o no tiene get_solo
                lay = None
            except DatabaseError:
                logger.exception("Error DB al intentar Layout.get_solo()")
                lay = None

        except LookupError:
            # No existía Layout en las apps configuradas
            lay = None

        for modelo in modelos:
            if modelo._meta.model_name != "layout":
                lista_modelos.append(modelo.__name__)

        response = render(request, "mantenimiento/mantenimiento.html", {
            "lista_modelos": lista_modelos,
            "layo": lay
        })

        # Consumir mensajes (si querés)
        storage = messages.get_messages(request)
        storage.used = True
        return response

    except DatabaseError as e:
        logger.exception("Error de base de datos en f_mantenimiento: %s", e)
        messages.error(request, "Ocurrió un error al cargar el mantenimiento (DB).")
        return redirect("N_inicio")




# mantenimiento/views.py (fragmento)
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from mantenimiento import services, constants

logger = logging.getLogger(__name__)

@rol_required("Usuario", "Staff")
def f_mantenimientoB(request, modelo):
    # Intentamos resolver el modelo; si no existe, redirect con mensaje
    try:
        Modelo = services.get_model_by_name(modelo)
    except LookupError:
        messages.error(request, f"El modelo '{modelo}' no existe.")
        return redirect("N_mantenimiento")

    # Como hay 1 solo layout, redirigimos a el panel de mantenimiento
    if Modelo._meta.model_name in constants.MODELOS_ESPECIALES:
        return redirect("N_mantenimiento")

    # Parámetros GET
    search_query = request.GET.get("q", "").strip()
    sort_field_raw = request.GET.get("sort", "").strip()
    sort_order = request.GET.get("order", "asc").strip().lower()

    try:
        instancias, campo_mostrado, campo_mostrado_verbose, campos_para_template = \
            services.build_queryset_and_metadata(Modelo, search_query, sort_field_raw, sort_order)

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
    except (ValidationError, DatabaseError) as e:
        logger.exception("Error al cargar datos para %s: %s", modelo, e)
        messages.error(request, f"Ocurrió un error al cargar los datos de {modelo}.")
        return redirect("N_mantenimiento")


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import DatabaseError, transaction
from django import forms

from mantenimiento import services, constants

@never_cache
@rol_required("Usuario", "Staff")
def f_mantenimientoC(request, modelo, pk):
    try:
        Modelo = services.get_model_by_name(modelo)
    except LookupError:
        messages.error(request, f"El modelo '{modelo}' no existe.")
        return redirect("N_mantenimiento")

    instancia = get_object_or_404(Modelo, pk=pk)

    # Lista de modelos para el sidebar
    lista_modelos = [{"name": m.__name__} for m in services.list_models()]

    # Crear formulario con widgets dinámicos
    Formulario = services.create_modelform_with_widgets(Modelo)

    try:
        if request.method == "POST":
            if request.POST.get("accion") == "eliminar":
                # Proteger singleton Layout: no permitir eliminar desde la vista
                if Modelo._meta.model_name == "layout":
                    messages.error(request, "No se puede eliminar la instancia de Layout.")
                    return redirect("N_mantenimientoB", modelo=modelo)

                instancia.delete()
                messages.success(request, f"Se eliminó correctamente {str(instancia)}.")
                return redirect("N_mantenimientoB", modelo=modelo)

            form = Formulario(request.POST, request.FILES, instance=instancia)
            if form.is_valid():
                with transaction.atomic():
                    instancia_guardada = form.save(commit=False)

                    # Mantener o asignar usuario si el modelo tiene ese campo
                    field_names = [f.name for f in Modelo._meta.fields]
                    if 'usuario' in field_names:
                        instancia_guardada.usuario = getattr(instancia, 'usuario', request.user)

                    instancia_guardada.save()
                    form.save_m2m()

                messages.success(request, f"Se guardó correctamente {str(instancia)}.")
                if request.POST.get("accion") == "guardaryseguir":
                    return redirect("N_mantenimientoC", modelo=modelo, pk=pk)
                return redirect("N_mantenimientoB", modelo=modelo)
            else:
                messages.warning(request, "Por favor revisa los datos ingresados.")
        else:
            form = Formulario(instance=instancia)
            # Mostrar el usuario actual si el modelo lo tiene
            field_names = [f.name for f in Modelo._meta.fields]
            if 'usuario' in field_names:
                form.fields['usuario'] = forms.CharField(
                    label="Usuario",
                    required=False,
                    disabled=True,
                    initial=getattr(instancia.usuario, 'username', '') if getattr(instancia, 'usuario', None) else ''
                )

        template = "mantenimiento/mantenimientoC_layout.html" if Modelo._meta.model_name == "layout" else "mantenimiento/mantenimientoC.html"
        return render(request, template, {
            "form": form,
            "modelo": Modelo.__name__,
            "instancia": instancia,
            "lista_m": lista_modelos,
        })

    except DatabaseError as e:
        logger.exception("DB error editing %s pk=%s: %s", modelo, pk, e)
        messages.error(request, f"Ocurrió un error al procesar la edición de {modelo}.")
        return redirect("N_mantenimientoB", modelo=modelo)


@never_cache
@rol_required("Usuario", "Staff")
def crear(request, modelo):
    try:
        Modelo = services.get_model_by_name(modelo)
    except LookupError:
        messages.error(request, "El modelo especificado no existe.")
        return redirect("N_mantenimiento")

    if Modelo._meta.model_name in constants.MODELOS_ESPECIALES:
        messages.error(request, "Solo puede haber una instancia de ese modelo.")
        return redirect("N_mantenimiento")

    Formulario = services.create_modelform_with_widgets(Modelo)

    try:
        if request.method == 'POST':
            form = Formulario(request.POST, request.FILES)
            if form.is_valid():
                instancia = form.save(commit=False)
                field_names = [f.name for f in Modelo._meta.fields]
                if 'usuario' in field_names:
                    instancia.usuario = request.user
                instancia.save()
                form.save_m2m()

                accion = request.POST.get('accion')
                if accion == 'guardar':
                    messages.success(request, f"Se guardó correctamente {Modelo.__name__}.")
                    return redirect('N_mantenimientoB', modelo=modelo)
                elif accion == 'guardaryseguir':
                    messages.success(request, f"Se guardó correctamente {Modelo.__name__}. ¡Continúa editando!")
                    return redirect('N_crear', modelo=modelo)
            else:
                messages.warning(request, "Por favor revisa los datos ingresados.")
        else:
            form = Formulario()

        descripcion_modelo = getattr(Modelo, 'descripcion_modelo', None)
        return render(request, 'mantenimiento/crear.html', {
            'Modelo': modelo,
            'form': form,
            'descripcion_modelo': descripcion_modelo,
        })
    except DatabaseError as e:
        logger.exception("DB error creating %s: %s", modelo, e)
        messages.error(request, f"Ocurrió un error al crear un nuevo {modelo}.")
        return redirect("N_mantenimiento")


from django.db import DatabaseError

@never_cache
@rol_required("Usuario", "Staff")
def eliminar_varios(request, modelo):
    try:
        Modelo = services.get_model_by_name(modelo)
    except LookupError:
        messages.error(request, "Modelo no encontrado.")
        return redirect("N_mantenimiento")

    if request.method == "POST":
        ids = request.POST.getlist("seleccionados")
        if not ids:
            messages.warning(request, "No seleccionaste ningún elemento para eliminar.")
            return redirect("N_mantenimientoB", modelo=modelo)

        # Validar y convertir ids a enteros
        try:
            ids_clean = [int(i) for i in ids]
        except ValueError:
            messages.error(request, "IDs inválidos.")
            return redirect("N_mantenimientoB", modelo=modelo)

        try:
            eliminados_qs = Modelo.objects.filter(pk__in=ids_clean)
            cantidad = eliminados_qs.count()
            eliminados_qs.delete()
            messages.success(request, f"Se eliminaron {cantidad} {modelo}(s) correctamente.")
        except DatabaseError as e:
            logger.exception("Error DB al eliminar varios de %s: %s", modelo, e)
            messages.error(request, f"Ocurrió un error al eliminar elementos de {modelo}.")

    return redirect("N_mantenimientoB", modelo=modelo)
