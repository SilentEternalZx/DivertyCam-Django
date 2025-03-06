from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import*
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cliente
from .forms import ClienteForm
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from .models import Evento
from .forms import EventoForm
from django.contrib import messages


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
            messages.success(request, "Usuario creado con éxito")
            login(request, usuario)
            return redirect("index")

    return render(request, "register/register.html", {"mensaje": mensaje})


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

class ClienteCreateView(CreateView):  #LoginRequiredMixin,
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

class EventoListView(ListView):
    model = Evento
    context_object_name = 'eventos'
    paginate_by = 10
    template_name = 'eventos/evento_list.html'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        
        if q:
            # Búsqueda usando el vector de búsqueda
            search_query = SearchQuery(q)
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
            
            # Si no hay resultados con la búsqueda de texto completo, intentamos con LIKE
            if not queryset.exists():
                queryset = Evento.objects.filter(
                    Q(nombre__icontains=q) |
                    Q(cliente__nombre__icontains=q) |
                    Q(cliente__apellido__icontains=q) |
                    Q(direccion__icontains=q)
                )
                
        return queryset

class EventoDetailView(DetailView):
    model = Evento
    context_object_name = 'evento'
    template_name = 'eventos/evento_detail.html'

class EventoCreateView( SuccessMessageMixin, CreateView):  
    model = Evento
    form_class = EventoForm
    template_name = 'eventos/evento_form.html'
    success_url = reverse_lazy('evento_list')
    success_message = ("Evento creado exitosamente")

class EventoUpdateView(SuccessMessageMixin, UpdateView):
    model = Evento
    form_class = EventoForm
    template_name = 'eventos/evento_form.html'
    success_message = ("Evento actualizado exitosamente")
    
    def get_success_url(self):
        return reverse_lazy('evento_detail', kwargs={'pk': self.object.pk})

class EventoDeleteView(SuccessMessageMixin, DeleteView):
    model = Evento
    context_object_name = 'evento'
    template_name = 'eventos/evento_confirm_delete.html'
    success_url = reverse_lazy('evento_list')
    success_message = ("Evento eliminado exitosamente")



