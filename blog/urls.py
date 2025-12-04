from django.urls import path
from . import views


urlpatterns = [
path('articulos/',views.listar_articulos, name="N_articulos"),   
path('art/<str:Pagina_slug>/<int:Articulo_id>',views.cargar_Darticulo,name="N_articulo"),
path('sub/<str:Pagina_slug>/<str:SubCategoria_slug>',views.cargar_Psubcategorias, name="N_subcategoria"),
path('<str:Pagina_slug>/<int:Categoria_id>',views.cargar_Pcategorias, name= "N_categoria"),
]
