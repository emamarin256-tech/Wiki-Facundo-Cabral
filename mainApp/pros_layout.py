from .models import Layout

def layout(request):
    layout=Layout.get_solo()
    return {"l_titulo":layout.titulo,"l_logo":layout.logo}