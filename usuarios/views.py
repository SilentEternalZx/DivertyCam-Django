from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

from .models import User, Rol, Permiso

def index(request):
    return render(request, "index/index.html")

def login_view(request):
    mensaje = ""  # Mensaje de error si las credenciales fallan
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario")
        contraseña = request.POST.get("contraseña")
        usuario = authenticate(request, username=nombre_usuario, password=contraseña)

        if usuario is not None:
            login(request, usuario)
            return redirect("index")  # Redirige a la página principal tras iniciar sesión
        else:
            mensaje = "Usuario o contraseña inválidos"

    return render(request, "login/login.html", {"mensaje": mensaje})

# Cerrar sesión
@login_required
def logout_view(request):
    logout(request)
    messages.success(request,"Sesión cerrada con éxito")
    return redirect("login")  # Redirige a la página de login tras cerrar sesión

# Registro de usuarios
def register_view(request):
    mensaje = ""
    if request.method == "POST":
        nombre_usuario = request.POST.get("nombre_usuario")
        email = request.POST.get("email")
        contraseña = request.POST.get("contraseña")
        confirmacion = request.POST.get("confirmacion")

        if contraseña != confirmacion:
            
            mensaje = "Las contraseñas no coinciden"
        elif User.objects.filter(username=nombre_usuario).exists():
            mensaje = "El nombre de usuario ya está en uso"
        elif User.objects.filter(email=email).exists():
            mensaje = "El correo electrónico ya está en uso"
        else:
            usuario = User.objects.create_user(username=nombre_usuario, email=email, password=contraseña)
            usuario.save()
            login(request, usuario)
            return redirect("index")

    return render(request, "register/register.html", {"mensaje": mensaje})
# Obtener permisos de un usuario
@login_required
def obtener_permisos_usuario(request):
    permisos = request.user.roles.values_list("permisos__nombre", flat=True).distinct()
    return JsonResponse({"permisos": list(permisos)}, status=200)

# Asignar un rol a un usuario
@login_required
def asignar_rol_usuario(request, usuario_id, rol_id):
    try:
        usuario = User.objects.get(id=usuario_id)
        rol = Rol.objects.get(id=rol_id)
        usuario.roles.add(rol)
        return JsonResponse({"mensaje": "Rol asignado correctamente"}, status=200)
    except User.DoesNotExist:
        return JsonResponse({"mensaje": "Usuario no encontrado"}, status=404)
    except Rol.DoesNotExist:
        return JsonResponse({"mensaje": "Rol no encontrado"}, status=404)



