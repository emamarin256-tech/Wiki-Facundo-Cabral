from django.shortcuts import redirect
from django.contrib import messages

class RedirectNoSuperuser:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        if request.path.startswith('/admin/'):
            user = request.user
            
            if not user.is_authenticated or not user.is_superuser:
                messages.warning(request, "No tenés permiso para acceder al panel de administración.")
                return redirect('N_inicio_sesion')  
        return self.get_response(request)

class RangeRequestMiddleware:
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Agregar header para permitir Range Requests
        if request.path.startswith('/media/'):
            response['Accept-Ranges'] = 'bytes'
        return response