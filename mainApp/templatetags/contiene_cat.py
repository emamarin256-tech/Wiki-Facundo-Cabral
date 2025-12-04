from django import template

register = template.Library()

@register.filter
def contiene_categoria(categorias, valor):
    return any(cat[2] == valor for cat in categorias)

