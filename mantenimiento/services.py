# mantenimiento/services.py
import logging
from django.apps import apps
from django.db import DatabaseError
from django.core.exceptions import ValidationError
from django.db.models import Q
from django import forms

from mantenimiento import constants

logger = logging.getLogger(__name__)


def get_model_by_name(model_name: str):
    for app_label in constants.MODELOS_A_BUSCAR:
        # probar tanto como viene como con capitalizado (Django busca por class name)
        for candidate in (model_name, model_name.capitalize(), model_name.title()):
            try:
                model = apps.get_model(app_label, candidate)
                if model:
                    return model
            except LookupError:
                continue
    raise LookupError(f"Modelo '{model_name}' no encontrado en apps: {constants.MODELOS_A_BUSCAR}")


def list_models():
    """Retorna la lista de modelos de las apps configuradas."""
    lista = []
    for app_label in constants.MODELOS_A_BUSCAR:
        try:
            app_config = apps.get_app_config(app_label)
            lista.extend(app_config.get_models())
        except LookupError:
            continue
    return lista


def build_allowed_fields(Modelo):
    """
    Construye la lista de campos permitidos para mostrar/ordenar con
    la regla: incluir CharField solo si su name está en CAMPOS_BUSQUEDA,
    y otros tipos básicos.
    """
    allowed = []
    for campo in Modelo._meta.fields:
        tipo = campo.get_internal_type()
        if tipo == "CharField":
            if campo.name in constants.CAMPOS_BUSQUEDA:
                allowed.append(campo.name)
        elif tipo in ("DateField", "DateTimeField", "IntegerField", "FloatField", "BooleanField", "ForeignKey"):
            allowed.append(campo.name)
    return allowed


def build_queryset_and_metadata(Modelo, search_query: str, sort_field_raw: str, sort_order: str):
    """
    Aplica búsqueda y orden, valida parámetros y devuelve:
      - instancias (QuerySet)
      - campo_mostrado (str|None)
      - campo_verbose (str|None)
      - campos_para_template (list of dict)
    """
    instancias = Modelo.objects.all()

    # BÚSQUEDA
    if search_query:
        filtro_q = Q()
        for campo in constants.CAMPOS_BUSQUEDA:
            if campo in [f.name for f in Modelo._meta.get_fields()]:
                filtro_q |= Q(**{f"{campo}__istartswith": search_query})
        if filtro_q.children:
            instancias = instancias.filter(filtro_q)

    # CAMPOS PERMITIDOS
    allowed_fields = build_allowed_fields(Modelo)

    # VALIDAR sort_order
    sort_order = (sort_order or "asc").lower()
    if sort_order not in ("asc", "desc"):
        sort_order = "asc"

    campo_mostrado = None
    if sort_field_raw:
        if sort_field_raw in allowed_fields:
            campo_para_ordenar = f"-{sort_field_raw}" if sort_order == "desc" else sort_field_raw
            try:
                instancias = instancias.order_by(campo_para_ordenar)
                campo_mostrado = sort_field_raw
            except Exception as e:
                # Si falla el order_by por cualquier razón, loguearlo y seguir sin ordenar
                logger.warning("Ordenamiento falló: %s", e, exc_info=True)

    campo_mostrado_verbose = None
    if campo_mostrado:
        for campo in Modelo._meta.fields:
            if campo.name == campo_mostrado:
                campo_mostrado_verbose = campo.verbose_name
                break

    mapa_verbose = {f.name: f.verbose_name for f in Modelo._meta.fields}
    campos_para_template = [{
        "name": nombre,
        "verbose": mapa_verbose.get(nombre, nombre.replace("_", " ").capitalize())
    } for nombre in allowed_fields]

    return instancias, campo_mostrado, campo_mostrado_verbose, campos_para_template


def create_modelform_with_widgets(Modelo):
    from django.forms import modelform_factory
    from django_ckeditor_5.widgets import CKEditor5Widget
    from django_select2.forms import Select2MultipleWidget

    widgets = {}



    

    for field in Modelo._meta.get_fields():
        # TextField → CKEditor 5
        if (
            getattr(field, "get_internal_type", lambda: "")() == "TextField"
            and CKEditor5Widget is not None
        ):
            widgets[field.name] = CKEditor5Widget(
                config_name="default"  # o el config que tengas definido
            )

        # ManyToMany → Select2
        elif getattr(field, "many_to_many", False) and Select2MultipleWidget is not None:
            widgets[field.name] = Select2MultipleWidget()

    return modelform_factory(
        Modelo,
        fields="__all__",
        widgets=widgets
    )

