# Wiki-Facundo-Cabral

Aplicación web en Django para la gestión colaborativa de contenido, con sistema de roles para colaboradores del sitio, panel de mantenimiento personalizado y soporte multimedia. Funciona como plantilla genérica reutilizable, con datos de ejemplo basados en Facundo Cabral.

### Requisito recomendado: Python 3.12

## Características
- Registro e inicio de sesión.
- Sistema de roles y permisos: **ingresante**, **usuario**, **staff** (y **superuser**).
  - **Ingresante:** rol por defecto al registrarse; solicita acceso para convertirse en usuario.
  - **Usuario:** puede gestionar modelos de la página (artículo, categoría, subcategoría, página, layout, tipo) desde el panel de mantenimiento. No accede a `/admin` ni gestiona usuarios.
  - **Staff:** además de las capacidades de usuario, accede a `/admin` y puede gestionar usuarios (aceptar/descender ingresantes, activar, eliminar, cambiar contraseña). Un staff **no** puede modificar a otro staff.
  - **Superuser:** puede editar cualquier staff.
- Creación automática de los 3 roles al iniciar el servidor; si se crea un superuser se le asigna automáticamente el rol `staff`.
- Panel de mantenimiento (frontend) para gestionar modelos de la página.

## Modelos principales
- **Layout:** título y logo del sitio; nombre del panel de admin coincidiendo con el de la página.
- **Página:** visibles en la barra de navegación. Si no tienen contenido, redirigen a inicio. Pueden contener categorías, subcategorías y artículos.
- **Categoría:** se muestran en un menú desplegable; normalmente listan subcategorías o artículos.
- **Subcategoría:** muestra artículos o su propio contenido (mínimo: descripción o video).
- **Tipo:** relaciona páginas con artículos.
- **Artículo:** visible dentro de categoría y subcategoría; dependiendo del `tipo` se define en que pagina se muestra.

## Campos especiales
- Texto enriquecido con CKEditor 5.
- Videos vía URL (django-embed-video) o archivo (FileField).
- Miniatura automática a partir del video (URL o archivo) o manual mediante un archivo cargado.

## Pequeñas funcionalidades
- **Página de inicio:** si este campo está marcado, la página utiliza un slug vacío y actúa como punto de redirección.
- **Slug automático:** generado a partir del título si se deja vacío.
- **Manejo de duplicados:** control de duplicados en título y slug.


## Robustez
- Manejo de errores con página 404, mensajes y redirecciones.
- Tests: ~82 tests que cubren la mayoría de funcionalidades.
```bash
# Luego de la instalación corre los tests 
python manage.py test
```
## Instalación (plantilla genérica)
```bash
# si quieres usar un ambiente (Opcional):
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
# Finalmente ejecuta el servidor
python manage.py runserver
```


## Instalación (datos de prueba)

Si no quieres crear datos manualmente, puedes instalar datos de prueba.

Incluye páginas, categorías, artículos, etc., y **3 usuarios** para probar el sistema de roles:

### Usuarios
#### **Nombre de usuario:** *Rol* 
- **Dueño:** *Superuser*  
- **colaborador1:** *Usuario*  
- **colaborador1:** *Usuario*  

**Contraseña para todos los usuarios:** `test1234`

Descarga y pega la carpeta **media** en la raíz del repositorio:  
https://drive.google.com/drive/folders/1zVN4iIBDji1cN3BNWlWZu-Qo8pXVDz5o?usp=drive_link

```bash
# si quieres usar un ambiente (Opcional):
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py loaddata blog/fixtures/01_Tipo.json
python manage.py loaddata AppPagina/fixtures/02_Pagina.json
python manage.py loaddata blog/fixtures/03_Categoria.json
python manage.py loaddata blog/fixtures/04_blog_resto.json
python manage.py collectstatic

# Finalmente ejecuta el servidor
python manage.py runserver
```

## Accesos principales
- **Inicio de sesión / registro:** desde el menú desplegable de usuario.
- **Panel de mantenimiento:** disponible para usuarios con rol distinto de ingresante; accesible desde el menú desplegable o la página de usuario.
- **Panel de administración Django (`/admin`):** solo para staff y superuser; accesible vía `/admin` o desde la página de usuario.


### Proyecto finalizado. No se aceptan Pull Requests externos.


## Contacto
Para preguntas, sugerencias o feedback, utilizá la sección **Discussions** del repositorio.

Contacto profesional: emamarin256@gmail.com
