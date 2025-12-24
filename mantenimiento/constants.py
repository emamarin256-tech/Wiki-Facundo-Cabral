# mantenimiento/constants.py

# apps donde buscar modelos dinámicamente (orden preferido)
MODELOS_A_BUSCAR = ["blog", "AppPagina"]

# modelos especiales (usar lowercase para comparar con model._meta.model_name)
MODELOS_ESPECIALES = {"layout"}

# campos recomendados para búsqueda (centralizados)
CAMPOS_BUSQUEDA = ("nombre", "titulo")
