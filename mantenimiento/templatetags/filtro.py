from django import template
from django.utils.safestring import mark_safe
from django.db.models import ManyToManyField, ForeignKey
from django.forms.models import ModelChoiceField, ModelMultipleChoiceField
register = template.Library()

@register.filter
def attr(obj, attr_path):
    try:
        for part in attr_path.split('.'):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj
    except Exception:
        return None
    
from django.utils.formats import localize

@register.filter(is_safe=True)
def prer(value, mode="text"):
    if isinstance(value, bool):
        return mark_safe('<i class="fa-solid fa-check"></i>' if value else '<i class="fa-solid fa-xmark"></i>')
        

    if value is None:
        return ""

    return localize(value)


@register.filter
def es_manytomany(field):
    """
    Devuelve True si el BoundField corresponde a un campo de selección múltiple
    relacionado con un queryset de modelo (ModelMultipleChoiceField).
    """
    try:
        form_field = getattr(field, 'field', field)
        return isinstance(form_field, ModelMultipleChoiceField)
    except Exception:
        return False

@register.filter
def es_foreignkey(field):
    """
    Devuelve True si el BoundField corresponde a un campo de selección simple
    relacionado con un queryset de modelo (ModelChoiceField).
    """
    try:
        form_field = getattr(field, 'field', field)
        return isinstance(form_field, ModelChoiceField)
    except Exception:
        return False

@register.filter
def modelo_relacionado(field):
    """Devuelve el nombre del modelo relacionado para ForeignKey o ManyToMany."""
    try:
        form_field = getattr(field, 'field', field)
        qs = getattr(form_field, 'queryset', None)
        if qs is not None:
            model = getattr(qs, 'model', None)
            return model._meta.model_name if model else ''
    except Exception:
        pass
    return ''