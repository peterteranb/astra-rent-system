import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Formato JSON inválido.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'message': 'Sesión iniciada con éxito.'}, status=200)
    else:
        # Alternativa E2
        return JsonResponse({'error': 'Usuario o contraseña incorrectos'}, status=401)


@require_POST
def logout_view(request):
    logout(request)
    return JsonResponse({'message': 'Sesión cerrada correctamente.'}, status=200)