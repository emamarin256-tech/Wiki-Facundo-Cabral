import re
from django import template

register = template.Library()

@register.filter(name="regex")
def regex(value, pattern):
    """
    Devuelve True si el patrón regex aparece en el valor.
    Ejemplo: {{ texto|regex_search:"[A-Z]" }}
    """
    if not isinstance(value, str):
        return False
    try:
        return re.search(pattern, value) is not None
    except re.error:
        return False
