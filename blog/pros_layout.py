from blog.models import Layout

def layout(request):
    layout=Layout.get_solo()
    return {"V_titulo":layout.titulo,"V_logo":layout.logo}