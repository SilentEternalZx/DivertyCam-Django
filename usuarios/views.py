from urllib import request
from django.utils import timezone
from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import*
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ClienteForm, EventoForm
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from .models import Evento, ConfiguracionPhotobooth
from .forms import ConfiguracionPhotoboothForm


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


    # Lista de clientes
class ClienteListView(ListView):   #LoginRequiredMixin
    model = Cliente
    context_object_name = 'clientes'
    template_name = 'clientes/cliente_list.html'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(activo=True)  # Solo clientes activos
        query = self.request.GET.get('q')
        mostrar_inactivos = self.request.GET.get('mostrar_inactivos')
        
        # Si se solicita mostrar inactivos, no aplicamos el filtro de activo=True
        if mostrar_inactivos:
            queryset = super().get_queryset()
        
        if query:
            # Tu código de búsqueda existente...
            search_query = SearchQuery(query)
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
            
            if not queryset.exists():
                if mostrar_inactivos:
                    queryset = Cliente.objects.filter(
                        Q(nombre__icontains=query) |
                        Q(apellido__icontains=query) |
                        Q(cedula__icontains=query) |
                        Q(correo__icontains=query) |
                        Q(telefono__icontains=query)
                    )
                else:
                    queryset = Cliente.objects.filter(
                        Q(nombre__icontains=query) |
                        Q(apellido__icontains=query) |
                        Q(cedula__icontains=query) |
                        Q(correo__icontains=query) |
                        Q(telefono__icontains=query),
                        activo=True
                    )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_inactivos'] = self.request.GET.get('mostrar_inactivos', False)
        return context

class ClienteDetailView(DetailView):   #LoginRequiredMixin
    model = Cliente
    context_object_name = 'cliente'
    template_name = 'clientes/cliente_detail.html'

class ClienteCreateView(CreateView):  #LoginRequiredMixin,
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')
   

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cliente creado exitosamente")
        return response
    
     
    
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


class ClienteActivarView(ListView):
    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        cliente.activo = True
        cliente.save()
        messages.success(request, f"El cliente {cliente.nombre} {cliente.apellido} ha sido reactivado.")
        return redirect('cliente_list')

class ClienteInactivarView(ListView):
    def post(self, request, pk):
        cliente = get_object_or_404(Cliente, pk=pk)
        cliente.activo = False
        cliente.save()
        messages.success(request, f"El cliente {cliente.nombre} {cliente.apellido} ha sido marcado como inactivo.")
        return redirect('cliente_list')

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
    
    
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'fecha_hora', 'direccion', 'cliente', 'servicios']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'servicios': forms.CheckboxSelectMultiple(),
            }
    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        
        # Verificamos si la fecha es en el pasado
        if fecha_hora < timezone.now():
            raise forms.ValidationError("La fecha y hora no puede ser en el pasado.")
    
        return fecha_hora
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra solo clientes activos
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)

class EventoCreateView( SuccessMessageMixin, CreateView):  
    model = Evento
    form_class = EventoForm
    template_name = 'eventos/evento_form.html'
    success_url = reverse_lazy('evento_list')
   
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Evento creado exitosamente")
        return response

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
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Evento eliminado exitosamente")
        return response

# Añade estas vistas a tu archivo views.py


#@login_required
def configurar_photobooth(request, evento_id):
    """Vista para configurar el photobooth para un evento específico"""
    evento = get_object_or_404(Evento, pk=evento_id)
    
    # Obtener o crear la configuración
    config, created = ConfiguracionPhotobooth.objects.get_or_create(evento=evento)
    
    if request.method == 'POST':
        form = ConfiguracionPhotoboothForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuración del photobooth guardada exitosamente")
            return redirect('photobooth_preview', evento_id=evento.id)
    else:
        form = ConfiguracionPhotoboothForm(instance=config)
    
    return render(request, 'photobooth/configurar_photobooth.html', {
        'form': form,
        'evento': evento,
        'config': config
    })

#@login_required
def photobooth_preview(request, evento_id):
    """Vista previa del photobooth para un evento"""
    evento = get_object_or_404(Evento, pk=evento_id)
    
    try:
        config = ConfiguracionPhotobooth.objects.get(evento=evento)
    except ConfiguracionPhotobooth.DoesNotExist:
        messages.warning(request, "No hay configuración de photobooth. Por favor, configure primero.")
        return redirect('configurar_photobooth', evento_id=evento.id)
    
    return render(request, 'photobooth/preview_photobooth.html', {
        'evento': evento,
        'config': config
    })

def launch_photobooth(request, evento_id):
    """Lanzar el photobooth para uso por los invitados"""
    evento = get_object_or_404(Evento, pk=evento_id)
    
    try:
        config = ConfiguracionPhotobooth.objects.get(evento=evento)
    except ConfiguracionPhotobooth.DoesNotExist:
        return render(request, 'photobooth/error.html', {
            'mensaje': "Este evento no tiene configurado un photobooth."
        })
    
    return render(request, 'photobooth/launch_photobooth.html', {
        'evento': evento,
        'config': config
    })

def photobooth_collage(request, evento_id):
    """Vista para crear collage de fotos"""
    evento = get_object_or_404(Evento, pk=evento_id)
    
    try:
        config = ConfiguracionPhotobooth.objects.get(evento=evento)
    except ConfiguracionPhotobooth.DoesNotExist:
        return render(request, 'photobooth/error.html', {
            'mensaje': "Este evento no tiene configurado un photobooth."
        })
    
    return render(request, 'photobooth/collage.html', {
        'evento': evento,
        'config': config
    })
