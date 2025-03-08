from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import*
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cliente
from .forms import ClienteForm, FotografiaForm, RegistroForm
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
import requests


def index(request):  #Función  para retornar vista principal
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

    return render(request, "login/login.html", {
        "mensaje": mensaje
        })

# Cerrar sesión
@login_required
def logout_view(request):
    logout(request)
   
    return redirect("login")  # Redirige a la página de login tras cerrar sesión




def register_view(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # 🔹 Iniciar sesión automáticamente después del registro
            return redirect("index")
        else:
            print("❌ Errores del formulario:", form.errors)  # 🔹 Imprimir errores en la terminal
    else:
        form = RegistroForm()

    return render(request, "register/register.html", {"form": form})

def descargar_foto(request):
    return render(request,"fotografias/descargarFoto.html")

class ClienteListView( ListView):  #LoginRequiredMixin
    model = Cliente
    context_object_name = 'clientes'
    template_name = 'clientes/cliente_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        
        if query:
            # Búsqueda utilizando el vector de búsqueda de PostgreSQL para mejores resultados
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
            
            # Si no hay resultados con búsqueda de texto completo, intentamos con búsqueda simple
            if not queryset.exists():
                queryset = Cliente.objects.filter(
                    Q(nombre__icontains=query) |
                    Q(apellido__icontains=query) |
                    Q(cedula__icontains=query) |
                    Q(correo__icontains=query) |
                    Q(telefono__icontains=query)
                )
        
        return queryset

class ClienteDetailView(DetailView):   #LoginRequiredMixin
    model = Cliente
    context_object_name = 'cliente'
    template_name = 'clientes/cliente_detail.html'

class ClienteCreateView( CreateView):  #LoginRequiredMixin,
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

class ClienteUpdateView( UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')

class ClienteDeleteView( DeleteView):   #LoginRequiredMixin,
    model = Cliente
    context_object_name = 'cliente'
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')
    
def lista_fotos(request):
    fotos = Fotografia.objects.all()
    return render(request, "fotografias/foto_list.html", {"fotografias": fotos})

def subir_foto(request):
    if request.method == "POST":
        form = FotografiaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("lista_fotos")  # Redirige a la lista de fotos
    else:
        form = FotografiaForm()
    return render(request, "fotografias/subir_foto.html", {"form": form})

def publicar_foto_facebook(request, foto_id):
    foto = get_object_or_404(Fotografia, id=foto_id)
    page_id = settings.FACEBOOK_PAGE_ID  # 📌 Obtiene el Page ID desde settings.py
    access_token = settings.FACEBOOK_ACCESS_TOKEN  # 📌 Obtiene el Token de Página

    # Reemplazar la URL local con la de ngrok
    imagen_url = request.build_absolute_uri(foto.img.url).replace(
        "http://127.0.0.1:8000", "https://5782-190-130-105-253.ngrok-free.app"
    )

    url = f"https://graph.facebook.com/v22.0/{page_id}/photos"
    payload = {
        "url": imagen_url,  # URL pública de la imagen
        "caption": Fotografia.descripcion,
        "access_token": access_token
    }

    response = requests.post(url, data=payload)
    print(response.json())  # 📌 Ver la respuesta de Facebook en la terminal

    if response.status_code == 200:
        print("✅ Foto publicada en la página DivertyApp correctamente.")
        return redirect("lista_fotos")
    else:
        print("❌ Error al publicar en Facebook:", response.json())  
        return render(request, "error.html", {"error": response.json()})