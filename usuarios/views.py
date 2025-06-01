# Importaciones necesarias para views.py
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from urllib import request
from django.utils import timezone
from django import forms

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, StreamingHttpResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.contrib import messages
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from .models import Evento, PhotoboothConfig, CollageTemplate, CollageSession, SessionPhoto, CollageResult, Cliente
from .forms import ClienteForm, RegistroForm, EventoForm,AñadirFotoForm, PhotoboothConfigForm
import json
import uuid
import base64
import os
import tempfile
import io
import datetime
import logging
from django.contrib.auth.views import PasswordResetView
from django.core.exceptions import ObjectDoesNotExist
import requests
import win32print
import win32ui
import win32con
import cv2
import time
from PIL import Image, ImageDraw, ImageFont, ImageWin

# Configuración de logging
logger = logging.getLogger(__name__)



class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    
  
        


def index(request):  #Función  para retornar vista principal
    return render(request, "index/index.html")

def about(request):  #Función  para retornar vista principal
    return render(request, "index/about.html")

@csrf_exempt
def vista_login(request): #Función para iniciar sesión
   
    if request.method == "POST":  #Si la petición es un POST, capturar los datos
        nombre_usuario = request.POST.get("nombre_usuario")
        contraseña = request.POST.get("contraseña")
        usuario = authenticate(request, username=nombre_usuario, password=contraseña)
        
       


        if usuario is not None:  #Si el usuario existe
            login(request, usuario) #Logearse
            return redirect("index")  # Redirige a la página principal tras iniciar sesión
        else:  #De lo contrario mostrar mensaje de error
            messages.error(request,"El usuario o la contraseña son incorrectos")

    return render(request, "login/login.html")

# Cerrar sesión
@login_required
def vista_logout(request): #Función para cerrar sesión
   
    
    logout(request)
   
    return redirect("login")  # Redirige a la página de login tras cerrar sesión

@csrf_exempt
def register_view(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            # Validar si el usuario ya existe
            if User.objects.filter(username=username).exists():
                messages.error(request, "El nombre de usuario ya está registrado. Por favor elige otro.")
                return render(request, "register/register.html", {"form": form})
            if User.objects.filter(email=email).exists():
                messages.error(request, "El correo electrónico ya está registrado. Por favor usa otro.")
                return render(request, "register/register.html", {"form": form})
            usuario = form.save()
            login(request, usuario)  # 🔹 Iniciar sesión automáticamente después del registro
            return redirect("index")
        else:
            print("❌ Errores del formulario:", form.errors)  # 🔹 Imprimir errores en la terminal
    else:
        form = RegistroForm()

    return render(request, "register/register.html", {"form": form})

@csrf_exempt
def verificar_usuario(request):
    username = request.GET.get("username", "").strip()

    if not username:  # 📌 Si no se envió un usuario, devolver error JSON
        return JsonResponse({"error": "No se proporcionó un nombre de usuario"}, status=400)

    existe = User.objects.filter(username=username).exists()
    
    return JsonResponse({"existe": existe})  # 📌 Devuelve JSON válido

def verificar_email(request):
    email = request.GET.get("email", "").strip()

    if not email:  # 📌 Si no se proporciona un email, devolver un error
        return JsonResponse({"error": "No se proporcionó un email"}, status=400)

    existe = User.objects.filter(email=email).exists()
    return JsonResponse({"existe": existe})  # 📌 Devuelve `true` si el email ya está registrado


def descargar_foto(request, evento_id): #Función para retornar vista de fotografías de un evento
    if not request.user.is_authenticated:  #Si el usuario no está autenticado....
        return redirect("login") #Redirigir al login

    evento=Evento.objects.get(id=evento_id) #Obtener un evento en específico
 
    imagenes=evento.fotografias.all()  #Obtener todas las fotografías de un evento
    return render(request,"fotografias/descargar_foto.html",{
        "evento":evento,
        "imagenes":imagenes,
        
         
    })



def eventos_cliente(request): 
    if not request.user.is_authenticated: #Verificar si el usuario está logeado, de lo contrario retornar al login
        return redirect("login")
    
    try:
        cliente = Cliente.objects.get(usuario=request.user)  #Intentar obtener un cliente relacionado al usuario
    except ObjectDoesNotExist:  #De lo contrario 
        mensaje = "El usuario no tiene un cliente asignado"  #Retornar mensaje
        return render(request, "eventos/partials/table.html", {
            "mensaje": mensaje
        })
    
    eventos = cliente.eventos.all()  #Obtener todos los eventos de un cliente específico

    if not eventos.exists():   #Si no existe ningún evento asociado, retornar mensaje
        return render(request, "eventos/partials/table.html", {
            "mensaje": "No tiene eventos actualmente"
        })
    
    # --- FILTRO POR BÚSQUEDA ---
    query = request.GET.get('q')
    if query:
        eventos = eventos.filter(
            Q(nombre__icontains=query)
        )

    # --- ORDENAMIENTO ---
    orden = request.GET.get('orden')
    if orden == 'nombre':
        eventos = eventos.order_by('nombre')
    elif orden == 'nombre_desc':
        eventos = eventos.order_by('-nombre')
    elif orden == 'cliente':
        eventos = eventos.order_by('cliente__nombre')
    elif orden == 'cliente_desc':
        eventos = eventos.order_by('-cliente__nombre')
    elif orden == 'fecha_hora':
        eventos = eventos.order_by('fecha_hora')
    elif orden == 'fecha_hora_desc':
        eventos = eventos.order_by('-fecha_hora')

    # Evento e imágenes para vista previa (por ejemplo, el primero)
    evento = eventos.first()
    imagenes = evento.fotografias.all() if evento else []
    
    #Retornar vista con respectivos contextos

    return render(request, "eventos/eventos_cliente.html", {
        "evento": evento,
        "imagenes": imagenes,
        "eventos": eventos
    })

class ClienteListView(LoginRequiredMixin, ListView):  
    
    model = Cliente
    context_object_name = 'clientes'
    template_name = 'clientes/cliente_list.html'
    paginate_by = 10
    login_url = 'login'
    
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
                      
                        Q(telefono__icontains=query)
                    )
                else:
                    queryset = Cliente.objects.filter(
                        Q(nombre__icontains=query) |
                        Q(apellido__icontains=query) |
                        Q(cedula__icontains=query) |
                    
                        Q(telefono__icontains=query),
                        activo=True
                    )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_inactivos'] = self.request.GET.get('mostrar_inactivos', False)
        return context

class ClienteDetailView(LoginRequiredMixin, DetailView):   #LoginRequiredMixin
    model = Cliente
    context_object_name = 'cliente'
    template_name = 'clientes/cliente_detail.html'
    login_url = 'login'

class ClienteCreateView(LoginRequiredMixin, CreateView):  #LoginRequiredMixin,
    
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')
    login_url = 'login'
   

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Cliente creado exitosamente")
        return response
    
     
    
class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('cliente_list')
    login_url = 'login'

class ClienteDeleteView(LoginRequiredMixin, DeleteView):   #LoginRequiredMixin,
    model = Cliente
    context_object_name = 'cliente'
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')
    login_url = 'login'
    


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

#Mostrar las fotos guardadas
def lista_fotos(request):
    if not request.user.is_authenticated:
        return redirect("login")
    fotos = Fotografia.objects.all()
    return render(request, "fotografias/foto_list.html", {"fotografias": fotos})

# Subir fotos de los eventos
def subir_foto(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.method == "POST":
        form = AñadirFotoForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.usuario = request.user
            if not foto.evento:
                foto.evento = Evento.objects.first()
            foto.save()
            # Asociar los invitados seleccionados a la fotografía
            invitados = form.cleaned_data.get('invitados')
            if invitados:
                foto.invitados.set(invitados)
            return redirect("lista_fotos")
        else:
            print("Errores en el formulario:", form.errors)
    else:
        form = AñadirFotoForm()
    return render(request, "fotografias/subir_foto.html", {"form": form})
def listar_categorias(request):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista que muestra todas las categorías de eventos."""
    categorias = CategoriaEvento.objects.all()
    return render(request, "fotografias/lista_categorias.html", {"categorias": categorias})

def listar_eventos(request, categoria_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista que muestra los eventos de una categoría específica."""
    categoria = get_object_or_404(CategoriaEvento, id=categoria_id)
    eventos = Evento.objects.filter(categoria=categoria)
    return render(request, "fotografias/lista_eventos.html", {"categoria": categoria, "eventos": eventos})

def listar_fotos_evento(request, evento_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista que muestra las fotos de un evento y permite enviarlas en bloque."""
    evento = get_object_or_404(Evento, id=evento_id)
    fotos = Fotografia.objects.filter(evento=evento)
    return render(request, "fotografias/lista_fotos.html", {"evento": evento, "fotos": fotos})

def publicar_album_facebook(request, evento_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Envía todas las fotos de un evento en bloque a Facebook."""
    evento = get_object_or_404(Evento, id=evento_id)
    fotos = Fotografia.objects.filter(evento=evento)

    if not evento.categoria or not evento.categoria.album_facebook_id:
        return JsonResponse({"error": "Este evento no tiene un álbum de Facebook asignado."}, status=400)

    album_id = evento.categoria.album_facebook_id
    access_token = settings.FACEBOOK_ACCESS_TOKEN

    errores = []
    for foto in fotos:
        imagen_url = request.build_absolute_uri(foto.img.url).replace(
            "http://127.0.0.1:8000", "https://55dc-191-156-43-126.ngrok-free.app"
        )

        payload = {
            "url": imagen_url,
            "caption": f"📸 {foto.descripcion} | 📅 {evento.fecha_hora.strftime('%d/%m/%Y')} | 📍 {evento.direccion}",
            "access_token": access_token
        }

        response = requests.post(f"https://graph.facebook.com/v22.0/{album_id}/photos", data=payload)
        data = response.json()

        if response.status_code != 200:
            errores.append(data)

    if errores:
        return JsonResponse({"error": errores}, status=400)
    return JsonResponse({"success": "Todas las fotos se publicaron correctamente en Facebook"})

#Envío de las fotos a facebook
def publicar_foto_facebook(request, foto_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Sube manualmente una foto a Facebook cuando el usuario presiona un botón."""
    foto = get_object_or_404(Fotografia, id=foto_id)
    evento = foto.evento

    # 📌 Verificar que el evento tenga una categoría asignada
    if not evento.categoria:
        return JsonResponse({"error": "Este evento no tiene una categoría asignada."}, status=400)

    # 📌 Verificar que la categoría tenga un `album_facebook_id`
    album_id = evento.categoria.album_facebook_id
    if not album_id:
        return JsonResponse({"error": "Esta categoría no tiene un álbum en Facebook asignado."}, status=400)

    # 📌 Obtener la URL pública de la imagen
    imagen_url = request.build_absolute_uri(foto.img.url).replace(
        "http://127.0.0.1:8000", " https://55dc-191-156-43-126.ngrok-free.app"
    )

    # 📌 Definir la descripción de la foto
    caption = f"📸 {foto.descripcion} | 📅 {evento.fecha_hora.strftime('%d/%m/%Y %H:%M')} | 📍 {evento.direccion} | Categoría: {evento.categoria.nombre}"

    # 📌 Hacer la solicitud a Facebook
    url = f"https://graph.facebook.com/v18.0/{album_id}/photos"
    payload = {
        "url": imagen_url,
        "caption": caption,
        "access_token": settings.FACEBOOK_ACCESS_TOKEN
    }

    response = requests.post(url, data=payload)
    data = response.json()

    if response.status_code == 200:
        return JsonResponse({"success": "Foto publicada correctamente en Facebook"})
    else:
        return JsonResponse({"error": data}, status=400)
   
class EventoListView(LoginRequiredMixin, ListView):
    model = Evento
    context_object_name = 'eventos'
    paginate_by = 10
    template_name = 'eventos/evento_list.html'
    login_url = 'login'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        q = self.request.GET.get('q')
        orden = self.request.GET.get('orden', 'fecha_hora')  # Orden por defecto

        # Búsqueda por vector de búsqueda
        if q:
            search_query = SearchQuery(q)
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
            
            # Si no hay resultados, usamos búsqueda con LIKE
            if not queryset.exists():
                queryset = Evento.objects.filter(
                    Q(nombre__icontains=q) |
                    Q(cliente__nombre__icontains=q) |
                    Q(cliente__apellido__icontains=q) |
                    Q(direccion__icontains=q)
                )

        # Ordenamiento dinámico
        if orden.endswith("_desc"):
            orden = "-" + orden.replace("_desc", "")  # Convierte 'nombre_desc' en '-nombre'

        queryset = queryset.order_by(orden)
        return queryset

class EventoDetailView(LoginRequiredMixin,DetailView):
    model = Evento
    context_object_name = 'evento'
    template_name = 'eventos/evento_detail.html'
    login_url = 'login'
    
    
class EventoForm(LoginRequiredMixin,forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['categoria','nombre', 'fecha_hora', 'direccion', 'cliente', 'servicios']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'servicios': forms.CheckboxSelectMultiple(),
            }
        login_url = 'login'
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
        
        if 'class' in self.fields['servicios'].widget.attrs:
            del self.fields['servicios'].widget.attrs['class']

class EventoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):  
    model = Evento
    form_class = EventoForm
    template_name = 'eventos/evento_form.html'
    success_url = reverse_lazy('evento_list')
    login_url = 'login'
   
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Evento creado exitosamente")
        return response

class EventoUpdateView(LoginRequiredMixin,SuccessMessageMixin, UpdateView):
    model = Evento
    form_class = EventoForm
    template_name = 'eventos/evento_form.html'
    success_message = ("Evento actualizado exitosamente")
    login_url = 'login'
    
    def get_success_url(self):
        return reverse_lazy('evento_detail', kwargs={'pk': self.object.pk})

class EventoDeleteView(LoginRequiredMixin,SuccessMessageMixin, DeleteView):
    model = Evento
    context_object_name = 'evento'
    template_name = 'eventos/evento_confirm_delete.html'
    success_url = reverse_lazy('evento_list')
    login_url = 'login'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Evento eliminado exitosamente")
        return response


@login_required
def configurar_photobooth(request, evento_id):
    """Vista mejorada para configurar el photobooth de un evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    config, created = PhotoboothConfig.objects.get_or_create(evento=evento)
    
    template_id = request.GET.get('template')
    
    if request.method == 'POST':
        # Depuración: imprime valores del POST
        print("POST data:", request.POST)
        
        form = PhotoboothConfigForm(
            request.POST, 
            request.FILES, 
            instance=config, 
            evento=evento
        )
        
        if form.is_valid():
            config = form.save(commit=False)
            config.evento = evento
            
            # Guardar el ID de la cámara seleccionada
            camera_id = request.POST.get('selected_camera_id')
            if camera_id:
                config.camera_id = camera_id
            
            # Guardar configuración de ISO, si existe en el POST
            iso_valor = request.POST.get('iso_valor')
            if iso_valor and iso_valor.isdigit():
                config.iso_valor = int(iso_valor)
            
            # Guardar la impresora seleccionada
            printer_name = request.POST.get('printer_name')
            if printer_name:
                config.printer_name = printer_name
            
            # Verificación explícita del campo de imagen
            if 'imagen_fondo' in request.FILES:
                config.imagen_fondo = request.FILES['imagen_fondo']
            
            # Guardar configuración de tiempos
            try:
                config.tiempo_entre_fotos = int(request.POST.get('tiempo_entre_fotos', 3))
                config.tiempo_cuenta_regresiva = int(request.POST.get('tiempo_cuenta_regresiva', 3))
                config.tiempo_visualizacion_foto = int(request.POST.get('tiempo_visualizacion_foto', 2))
            except (ValueError, TypeError):
                # Si hay error en la conversión, usar valores predeterminados
                config.tiempo_entre_fotos = 3
                config.tiempo_cuenta_regresiva = 3
                config.tiempo_visualizacion_foto = 2
            
            config.save()
            form.save_m2m()  # Para relaciones ManyToMany
            
            messages.success(request, "Configuración guardada correctamente")
            
            # Redirigir a la vista previa
            return redirect('preview_photobooth', evento_id=evento.id)
        else:
            print("Errores del formulario:", form.errors)
            messages.error(request, "Hay errores en el formulario. Por favor revise los campos.")
    else:
        # En caso de GET
        form = PhotoboothConfigForm(instance=config, evento=evento)
        
        # Si hay un template_id en la URL y no es un POST, actualizar valor inicial
        if template_id and not form.is_bound:
            try:
                template = CollageTemplate.objects.get(template_id=template_id, evento=evento)
                form.initial['plantilla_collage'] = template.template_id
                
                # Actualizar objeto config temporalmente para la vista previa
                if config is None:
                    config = PhotoboothConfig(evento=evento)
                config.plantilla_collage = template
            except CollageTemplate.DoesNotExist:
                pass
    
    # Obtener lista de impresoras para el selector
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    except:
        printers = []
    
    # Para la vista previa del collage
    selected_template = config.plantilla_collage
    frames = []
    if selected_template:
        frames = selected_template.get_frames()
    
    # Evitar error si los campos no existen aún
    try:
        print(f"Configuración actual: Resolución={config.resolucion_camara}, Balance={config.balance_blancos}, ISO={config.iso_valor}")
    except AttributeError:
        print("Advertencia: Algunos campos no existen aún en la base de datos")
    
    context = {
        'evento': evento,
        'form': form,
        'config': config,
        'selected_template': selected_template,
        'frames': frames,
        'printers': printers,
        # Añadir campos de agrupación para la plantilla
        'field_groups': form.field_groups if hasattr(form, 'field_groups') else None,
    }
    
    return render(request, 'photobooth/configurar_photobooth.html', context)



def preview_photobooth(request, evento_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para mostrar la vista previa del photobooth"""
    evento = get_object_or_404(Evento, id=evento_id)
    config = PhotoboothConfig.objects.filter(evento=evento).first()
    
    context = {
        'evento': evento,
        'config': config
    }
    
    return render(request, 'photobooth/preview_photobooth.html', context)

def launch_photobooth(request, evento_id):
    """Vista para iniciar el photobooth"""
    evento = get_object_or_404(Evento, id=evento_id)
    config = PhotoboothConfig.objects.filter(evento=evento).first()
    
    if not config:
        messages.warning(request, "El photobooth no está configurado completamente")
        return redirect('configurar_photobooth', evento_id=evento_id)
    
    # Crear una nueva sesión para CollageSession
    session = CollageSession.objects.create(
        evento=evento,
        template=config.plantilla_collage,
        session_id=str(uuid.uuid4()),
        status='active'
    )
    
    context = {
        'evento': evento,
        'config': config,
        'template': config.plantilla_collage,
        'template_json': json.dumps(json.loads(config.plantilla_collage.template_data)) if config.plantilla_collage and config.plantilla_collage.template_data else '{}',
        'session_id': session.session_id,
        'return_url': request.META.get('HTTP_REFERER', f'/eventos/{evento_id}/')
    }
    
    return render(request, 'photobooth/session.html', context)

def template_list(request, evento_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para listar las plantillas de collage disponibles para un evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    templates = CollageTemplate.objects.filter(evento=evento)

    # Procesar cada plantilla para extraer sus propiedades de visualización
    for template in templates:
        if template.template_data:
            try:
                data = json.loads(template.template_data)
                # Atributos para la visualización de la imagen de fondo
                template.bg_size = data.get('backgroundSize', template.background_size if hasattr(template, 'background_size') else 'cover')
                template.bg_position = data.get('backgroundPosition', template.background_position if hasattr(template, 'background_position') else 'center')
                template.bg_repeat = data.get('backgroundRepeat', template.background_repeat if hasattr(template, 'background_repeat') else 'no-repeat')
                
                # Extraer datos de los marcos
                frames = []
                for frame in data.get('frames', []):
                    frames.append(frame)
                template.frames = frames
            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Error procesando datos de plantilla: {str(e)}")
                template.bg_size = 'contain'  # Valor por defecto para mantener proporciones originales
                template.bg_position = 'center'
                template.bg_repeat = 'no-repeat'
                template.frames = []
    
    context = {
        'evento': evento,
        'templates': templates
    }
    
    return render(request, 'collage/template_list.html', context)

def template_editor(request, evento_id, template_id=None):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para el editor de plantillas de collage"""
    evento = get_object_or_404(Evento, id=evento_id)
    template = None
    
    if template_id:
        template = get_object_or_404(CollageTemplate, template_id=template_id, evento=evento)
    
    if request.method == 'POST':
        form = CollageTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            
            if not template_id:  # Nueva plantilla
                template.template_id = str(uuid.uuid4())
                template.evento = evento
            
            template.save()
            messages.success(request, "Plantilla guardada correctamente.")
            return redirect('template_list', evento_id=evento.id)
    else:
        form = CollageTemplateForm(instance=template)
    
    context = {
        'evento': evento,
        'form': form,
        'template': template
    }
    
    return render(request, 'collage/template_editor.html', context)

@csrf_exempt
@require_POST
def save_template(request):
    """API para guardar una plantilla de collage vía AJAX"""
    try:
        data = json.loads(request.body)
        
        evento_id = data.get('evento_id')
        if not evento_id:
            return JsonResponse({'success': False, 'error': 'ID de evento no proporcionado'})
        
        evento = get_object_or_404(Evento, id=evento_id)
        
        template_id = data.get('id')
        template_name = data.get('name')
        description = data.get('description', '')
        
        if not template_name:
            return JsonResponse({'success': False, 'error': 'Nombre de plantilla requerido'})
        
        # Crear nueva plantilla o actualizar existente
        if template_id:
            template = get_object_or_404(CollageTemplate, template_id=template_id, evento=evento)
        else:
            template_id = str(uuid.uuid4())
            template = CollageTemplate(template_id=template_id, evento=evento)
        
        template.nombre = template_name
        template.descripcion = description
        template.background_color = data.get('backgroundColor', '#FFFFFF')
        
        # Guardar propiedades del fondo
        template.background_size = data.get('backgroundSize', 'cover')
        template.background_position = data.get('backgroundPosition', 'center')
        template.background_repeat = data.get('backgroundRepeat', 'no-repeat')
        
        # Procesar imagen de fondo si se proporciona
        background_image = data.get('backgroundImage')
        if background_image and background_image.startswith('data:image'):
            format, imgstr = background_image.split(';base64,')
            ext = format.split('/')[-1]
            
            # Asegurarse de que existe el directorio destino
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'collage', 'backgrounds')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Crear un archivo temporal y guardarlo en la ubicación correcta
            image_data = base64.b64decode(imgstr)
            filename = f"{template_id}_bg.{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Guardar el archivo físicamente
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
            # Actualizar la ruta relativa en el modelo
            relative_path = os.path.join('collage', 'backgrounds', filename)
            template.background_image = relative_path
        
        # Guardar datos completos de la plantilla
        template.template_data = json.dumps(data)
        template.save()
        
        return JsonResponse({
            'success': True,
            'template_id': template.template_id
        })
        
    except Exception as e:
        logger.error(f"Error al guardar plantilla: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
    
def template_delete(request, evento_id, template_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para eliminar una plantilla de collage"""
    evento = get_object_or_404(Evento, id=evento_id)
    template = get_object_or_404(CollageTemplate, template_id=template_id, evento=evento)
    
    # Opcional: Verificar permisos
    
    # Eliminar la plantilla
    template.delete()
    
    # Mensaje de éxito
    messages.success(request, f"Plantilla '{template.nombre}' eliminada correctamente.")
    
    # Redireccionar a la lista de plantillas
    return redirect('template_list', evento_id=evento.id)

def get_template_data(request, template_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """API para obtener datos de una plantilla específica"""
    template = get_object_or_404(CollageTemplate, template_id=template_id)
    
    try:
        template_data = json.loads(template.template_data)
        return JsonResponse({
            'success': True,
            'template': template_data
        })
    except Exception as e:
        logger.error(f"Error al obtener datos de plantilla: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def start_session(request, evento_id, template_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Iniciar una sesión de fotos con una plantilla específica"""
    evento = get_object_or_404(Evento, id=evento_id)
    template = get_object_or_404(CollageTemplate, template_id=template_id, evento=evento)
    
    
    # Obtener la configuración del photobooth
    try:
        config = PhotoboothConfig.objects.get(evento=evento)
    except PhotoboothConfig.DoesNotExist:
        return render(request, 'photobooth/error.html', {
            'mensaje': 'No hay configuración para el photobooth. Por favor configúrela primero.'
        })
    
    # Convertir datos de la plantilla a JSON para JavaScript
    template_json = '{}'
    try:
        template_data = json.loads(template.template_data)
        template_json = json.dumps(template_data)
    except:
        template_json = '{}'
    
    # Crear una nueva sesión para esta sesión de photobooth
    session = CollageSession.objects.create(
        evento=evento,
        template=template,
        session_id=str(uuid.uuid4())
    )
    
    return render(request, 'photobooth/session.html', {
        'evento': evento,
        'config': config,
        'template': template,
        'template_json': template_json,
        'session_id': session.session_id,
        'return_url': request.META.get('HTTP_REFERER', f'/eventos/{evento_id}/photobooth/templates/')
    })

@csrf_exempt
@require_POST
def save_session_photo(request):
    """API para guardar una foto tomada durante la sesión"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        frame_index = data.get('frame_index')
        image_data = data.get('image_data')
        
        logger.info(f"Guardando foto para sesión {session_id}, frame {frame_index}")
        
        if not all([session_id, image_data, frame_index is not None]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Usar CollageSession directamente
        try:
            session = CollageSession.objects.get(session_id=session_id)
        except CollageSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Sesión con ID {session_id} no encontrada'})
        
        # Procesar la imagen base64
        if ',' in image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            decoded_image = base64.b64decode(imgstr)
            
            # Asegurar que existe el directorio destino
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'collage', 'session_photos')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre de archivo único
            filename = f"session_{session_id}_frame_{frame_index}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            # Guardar el archivo físicamente
            with open(filepath, 'wb') as f:
                f.write(decoded_image)
            
            # Crear o actualizar registro de foto
            try:
                photo = SessionPhoto.objects.filter(
                    session=session, 
                    frame_index=frame_index
                ).first()
                
                if photo:
                    # Actualizar foto existente
                    relative_path = os.path.join('collage', 'session_photos', filename)
                    photo.image = relative_path
                    photo.save()
                else:
                    # Crear nueva foto
                    relative_path = os.path.join('collage', 'session_photos', filename)
                    photo = SessionPhoto(
                        session=session,
                        frame_index=frame_index,
                        image=relative_path
                    )
                    photo.save()
                
                return JsonResponse({'success': True, 'photo_id': photo.id})
                
            except Exception as photo_error:
                logger.error(f"Error al guardar registro de foto: {str(photo_error)}")
                return JsonResponse({'success': False, 'error': f'Error al guardar registro: {str(photo_error)}'})
                
        else:
            return JsonResponse({'success': False, 'error': 'Formato de imagen no válido'})
        
    except Exception as e:
        logger.error(f"Error al guardar foto de sesión: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})

def session_result(request, session_id):
    """Vista para mostrar el resultado de una sesión de photobooth"""
    session = get_object_or_404(CollageSession, session_id=session_id)
    evento = session.evento
    template = session.template
    
    # Obtener todas las fotos de la sesión
    photos = SessionPhoto.objects.filter(session=session).order_by('frame_index')
    
    # Determinar si la sesión está completa
    template_data = json.loads(template.template_data) if template.template_data else {'frames': []}
    total_frames = len(template_data.get('frames', []))
    is_complete = photos.count() == total_frames
    
    # Obtener o crear el resultado del collage si está completo
    collage_result = None
    remaining_frames = []
    
    if is_complete:
        # Buscar un resultado existente o crear uno nuevo
        collage_result = CollageResult.objects.filter(session=session).first()
        
        if not collage_result and session.status == 'active':
            # Generar el collage si no existe
            collage_result = generate_collage(session, template_data, photos, template_data.get('frames', []))
            
            # Actualizar estado de la sesión
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
    else:
        # Calcular marcos restantes
        remaining_frames = range(total_frames - photos.count())
    
    return render(request, 'collage/session_result.html', {
        'evento': evento,
        'template': template,
        'photos': photos,
        'is_complete': is_complete,
        'collage_result': collage_result,
        'remaining_frames': remaining_frames,
        'session_id': session_id
    })

def generate_collage(session, template_data, photos, frames):
    """Genera una imagen de collage a partir de una sesión completada con mejor calidad y precisión"""
    try:
        # Asegurarse de que la sesión sea del tipo correcto
        if not isinstance(session, CollageSession):
            logger.error(f"Se esperaba una sesión del tipo CollageSession, pero se recibió {type(session)}")
            
            return None
        
                # Extraer dimensiones de la plantilla
        width_px = int(15 * 118.11)  # 10cm a 300dpi = 1181.1px
        height_px = int(10 * 118.11)  # 15cm a 300dpi = 1771.65px
        
        # Opcionalmente puede personalizarse con valores del template
        if 'width' in template_data and 'height' in template_data:
            try:
                width_px = int(float(template_data['width']))
                height_px = int(float(template_data['height']))
            except (ValueError, TypeError):
                pass  # Usar valores predeterminados si hay error
        
        # Crear imagen base para el collage
        background_color = template_data.get('backgroundColor', '#FFFFFF')
        if background_color.startswith('#'):
            r = int(background_color[1:3], 16)
            g = int(background_color[3:5], 16)
            b = int(background_color[5:7], 16)
            bg_color = (r, g, b, 255)
        else:
            bg_color = (255, 255, 255, 255)  # Blanco por defecto
        
        collage_img = Image.new('RGBA', (width_px, height_px), bg_color)
        
        # Si hay imagen de fondo en la plantilla, aplicarla
        if session.template.background_image:
            try:
                bg_img = Image.open(session.template.background_image.path)
                
                # Ajustar imagen de fondo según la configuración de la plantilla
                bg_size = template_data.get('backgroundSize', 'cover')
                bg_position = template_data.get('backgroundPosition', 'center')
                
                # Redimensionar imagen de fondo según el modo especificado
                if bg_size == 'cover':
                    # Escalar para cubrir completamente manteniendo proporción
                    bg_ratio = bg_img.width / bg_img.height
                    collage_ratio = width_px / height_px
                    
                    if bg_ratio > collage_ratio:
                        # Imagen más ancha que alta en proporción
                        new_height = width_px / bg_ratio
                        new_width = width_px
                        bg_img = bg_img.resize((int(new_width), int(new_height)), Image.LANCZOS)
                    else:
                        # Imagen más alta que ancha en proporción
                        new_width = height_px * bg_ratio
                        new_height = height_px
                        bg_img = bg_img.resize((int(new_width), int(new_height)), Image.LANCZOS)
                    
                elif bg_size == 'contain':
                    # Escalar para caber completamente manteniendo proporción
                    bg_ratio = bg_img.width / bg_img.height
                    collage_ratio = width_px / height_px
                    
                    if bg_ratio > collage_ratio:
                        # Imagen más ancha que alta en proporción
                        new_width = width_px
                        new_height = width_px / bg_ratio
                        bg_img = bg_img.resize((int(new_width), int(new_height)), Image.LANCZOS)
                    else:
                        # Imagen más alta que ancha en proporción
                        new_height = height_px
                        new_width = height_px * bg_ratio
                        bg_img = bg_img.resize((int(new_width), int(new_height)), Image.LANCZOS)
                    
                else:
                    # Modo stretch o tamaño personalizado
                    bg_img = bg_img.resize((width_px, height_px), Image.LANCZOS)
                
                # Convertir a RGBA para poder combinar con el fondo
                bg_img = bg_img.convert('RGBA')
                
                # Calcular posición para centrar la imagen
                pos_x = 0
                pos_y = 0
                
                if bg_img.width != width_px:
                    # Posicionar horizontalmente según bg_position
                    if 'left' in bg_position:
                        pos_x = 0
                    elif 'right' in bg_position:
                        pos_x = width_px - bg_img.width
                    else:  # center por defecto
                        pos_x = (width_px - bg_img.width) // 2
                
                if bg_img.height != height_px:
                    # Posicionar verticalmente según bg_position
                    if 'top' in bg_position:
                        pos_y = 0
                    elif 'bottom' in bg_position:
                        pos_y = height_px - bg_img.height
                    else:  # center por defecto
                        pos_y = (height_px - bg_img.height) // 2
                
                # Crear una nueva imagen para la mezcla
                positioned_bg = Image.new('RGBA', (width_px, height_px), (0, 0, 0, 0))
                positioned_bg.paste(bg_img, (pos_x, pos_y))
                
                # Mezclar con la imagen base
                collage_img = Image.alpha_composite(collage_img, positioned_bg)
                
            except Exception as e:
                logger.error(f"Error al aplicar imagen de fondo: {str(e)}")
        
        # Escala entre la resolución de plantilla (diseño) y la resolución de salida
        display_width = 378  # Ancho de diseño aproximado en píxeles (10cm a 96dpi)
        scale_factor = width_px / display_width
        
        # Colocar cada foto en su marco según la plantilla
        for photo in photos:
            try:
                # Obtener el marco correspondiente a esta foto
                frame = frames[photo.frame_index]
                
                # Extraer dimensiones y posición del marco (eliminar 'px' si está presente)
                frame_width = int(float(frame['width'].replace('px', '')))
                frame_height = int(float(frame['height'].replace('px', '')))
                frame_left = int(float(frame['left'].replace('px', '')))
                frame_top = int(float(frame['top'].replace('px', '')))
                
                # Escalar a dimensiones reales
                frame_width = int(frame_width * scale_factor)
                frame_height = int(frame_height * scale_factor)
                frame_left = int(frame_left * scale_factor)
                frame_top = int(frame_top * scale_factor)
                
                # Abrir foto y redimensionar para que encaje en el marco
                photo_img = Image.open(photo.image.path)
                photo_img = photo_img.resize((frame_width, frame_height), Image.LANCZOS)
                
                # Aplicar rotación si está especificada en el marco
                if 'rotation' in frame and frame['rotation']:
                    rotation_angle = float(frame['rotation'])
                    # Rotar alrededor del centro con fondo transparente
                    photo_img = photo_img.convert('RGBA')
                    photo_img = photo_img.rotate(rotation_angle, resample=Image.BICUBIC, expand=True)
                    
                    # Recalcular posición para centrar la imagen rotada
                    new_left = frame_left + (frame_width - photo_img.width) // 2
                    new_top = frame_top + (frame_height - photo_img.height) // 2
                    
                    # Crear una máscara para pegar la imagen rotada
                    mask = photo_img.split()[3]  # Canal alpha
                    
                    # Pegar la foto en la posición con máscara
                    collage_img.paste(photo_img, (new_left, new_top), mask)
                else:
                    # Pegar la foto en la posición original si no hay rotación
                    collage_img.paste(photo_img, (frame_left, frame_top))
                
                # Aplicar borde si está especificado en el marco
                if 'borderWidth' in frame and frame['borderWidth']:
                    try:
                        # Extraer propiedades del borde
                        border_width = int(float(frame['borderWidth'].replace('px', '')))
                        border_color = frame.get('borderColor', '#FFFFFF')
                        
                        # Escalar ancho del borde
                        border_width = int(border_width * scale_factor)
                        
                        # Convertir color a RGB
                        if border_color.startswith('#'):
                            r = int(border_color[1:3], 16)
                            g = int(border_color[3:5], 16)
                            b = int(border_color[5:7], 16)
                            border_rgb = (r, g, b)
                        else:
                            border_rgb = (255, 255, 255)  # Blanco por defecto
                        
                        # Dibujar borde alrededor de la foto
                        draw = ImageDraw.Draw(collage_img)
                        draw.rectangle(
                            [
                                (frame_left - border_width, frame_top - border_width),
                                (frame_left + frame_width + border_width, frame_top + frame_height + border_width)
                            ],
                            outline=border_rgb,
                            width=border_width
                        )
                    except Exception as border_error:
                        logger.error(f"Error al aplicar borde: {str(border_error)}")
                
            except Exception as photo_error:
                logger.error(f"Error al procesar foto {photo.id}: {str(photo_error)}")
        
        # Añadir elementos de texto si están definidos en la plantilla
        if 'textElements' in template_data and template_data['textElements']:
            for text_element in template_data['textElements']:
                try:
                    # Extraer propiedades del texto
                    text_content = text_element.get('text', '')
                    text_x = int(float(text_element.get('left', '0').replace('px', '')))
                    text_y = int(float(text_element.get('top', '0').replace('px', '')))
                    font_size = int(float(text_element.get('fontSize', '24').replace('px', '')))
                    font_family = text_element.get('fontFamily', 'Arial')
                    text_color = text_element.get('color', '#000000')
                    
                    # Escalar posición y tamaño
                    text_x = int(text_x * scale_factor)
                    text_y = int(text_y * scale_factor)
                    font_size = int(font_size * scale_factor)
                    
                    # Convertir color a RGB
                    if text_color.startswith('#'):
                        r = int(text_color[1:3], 16)
                        g = int(text_color[3:5], 16)
                        b = int(text_color[5:7], 16)
                        color_rgb = (r, g, b)
                    else:
                        color_rgb = (0, 0, 0)  # Negro por defecto
                    
                    # Cargar fuente
                    try:
                        # Intentar cargar fuente del sistema
                        font_path = f"fonts/{font_family}.ttf"
                        font = ImageFont.truetype(font_path, font_size)
                    except:
                        # Si falla, usar fuente por defecto
                        font = ImageFont.load_default()
                    
                    # Reemplazar variables en el texto
                    text_content = text_content.replace('{evento}', session.evento.nombre)
                    text_content = text_content.replace('{fecha}', session.evento.fecha_hora.strftime('%d/%m/%Y'))
                    text_content = text_content.replace('{hora}', session.evento.fecha_hora.strftime('%H:%M'))
                    text_content = text_content.replace('{cliente}', f"{session.evento.cliente.nombre} {session.evento.cliente.apellido}")
                    
                    # Dibujar texto
                    draw = ImageDraw.Draw(collage_img)
                    draw.text((text_x, text_y), text_content, fill=color_rgb, font=font)
                    
                except Exception as text_error:
                    logger.error(f"Error al procesar elemento de texto: {str(text_error)}")
        
        # Añadir elementos decorativos si están definidos en la plantilla
        if 'decorativeElements' in template_data and template_data['decorativeElements']:
            for element in template_data['decorativeElements']:
                try:
                    element_type = element.get('type', '')
                    element_x = int(float(element.get('left', '0').replace('px', '')))
                    element_y = int(float(element.get('top', '0').replace('px', '')))
                    element_width = int(float(element.get('width', '50').replace('px', '')))
                    element_height = int(float(element.get('height', '50').replace('px', '')))
                    element_color = element.get('color', '#000000')
                    
                    # Escalar posición y tamaño
                    element_x = int(element_x * scale_factor)
                    element_y = int(element_y * scale_factor)
                    element_width = int(element_width * scale_factor)
                    element_height = int(element_height * scale_factor)
                    
                    # Convertir color a RGB
                    if element_color.startswith('#'):
                        r = int(element_color[1:3], 16)
                        g = int(element_color[3:5], 16)
                        b = int(element_color[5:7], 16)
                        el_color_rgb = (r, g, b)
                    else:
                        el_color_rgb = (0, 0, 0)  # Negro por defecto
                    
                    # Dibujar elemento según su tipo
                    draw = ImageDraw.Draw(collage_img)
                    
                    if element_type == 'rectangle':
                        draw.rectangle(
                            [(element_x, element_y), (element_x + element_width, element_y + element_height)],
                            fill=el_color_rgb
                        )
                    elif element_type == 'circle':
                        draw.ellipse(
                            [(element_x, element_y), (element_x + element_width, element_y + element_height)],
                            fill=el_color_rgb
                        )
                    elif element_type == 'line':
                        line_end_x = element.get('endX', element_x + element_width)
                        line_end_y = element.get('endY', element_y + element_height)
                        line_width = int(float(element.get('lineWidth', '2').replace('px', '')))
                        
                        # Escalar
                        line_end_x = int(float(line_end_x) * scale_factor)
                        line_end_y = int(float(line_end_y) * scale_factor)
                        line_width = int(line_width * scale_factor)
                        
                        draw.line(
                            [(element_x, element_y), (line_end_x, line_end_y)],
                            fill=el_color_rgb,
                            width=line_width
                        )
                    
                except Exception as element_error:
                    logger.error(f"Error al procesar elemento decorativo: {str(element_error)}")
        
        # Añadir marca de agua del evento si está configurado
        # try:
        #     config = PhotoboothConfig.objects.get(evento=session.evento)
        #     if config.mostrar_marca_agua:
        #         draw = ImageDraw.Draw(collage_img)
        #         watermark_text = f"{session.evento.nombre} - {session.created_at.strftime('%d/%m/%Y')}"
                
        #         # Usar una fuente semi-transparente
        #         font = ImageFont.load_default()
        #         watermark_color = (128, 128, 128, 128)  # Gris semitransparente
                
        #         # Colocar en la esquina inferior derecha
        #         text_width, text_height = draw.textsize(watermark_text, font=font)
        #         position = (width_px - text_width - 10, height_px - text_height - 10)
                
        #         # Dibujar texto
        #         draw.text(position, watermark_text, fill=watermark_color, font=font)
        # except Exception as watermark_error:
        #     logger.error(f"Error al añadir marca de agua: {str(watermark_error)}")
        
       # Al guardar el resultado, usar la ruta correcta:
        collage_id = str(uuid.uuid4())
        img_io = io.BytesIO()
        
        # Si la imagen es RGBA, convertir a RGB para JPEG
        if collage_img.mode == 'RGBA':
            # Crear fondo blanco y componer con la imagen
            white_bg = Image.new('RGB', collage_img.size, (255, 255, 255))
            white_bg.paste(collage_img, (0, 0), collage_img)
            collage_img = white_bg
        
        # Guardar con alta calidad
        collage_img.save(img_io, format='JPEG', quality=95, optimize=True)
        img_content = img_io.getvalue()
        
        # Crear directorio si no existe
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'collage', 'results')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"collage_{collage_id}.jpg"
        
        # Crear registro en la base de datos
        collage_result = CollageResult(
            collage_id=collage_id,
            session=session
        )
        
        # Guardar el archivo en la ubicación especificada
        filepath = os.path.join(upload_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(img_content)
        
        # Asignar la ruta relativa al modelo
        relative_path = os.path.join('collage', 'results', filename)
        collage_result.image = relative_path
        collage_result.save()
        
        # Actualizar estadísticas
        try:
            config = PhotoboothConfig.objects.get(evento=session.evento)
            config.total_sesiones += 1
            config.total_fotos += len(photos)
            config.save()
        except:
            pass
        
        return collage_result
        
    except Exception as e:
        logger.error(f"Error al generar collage: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

@csrf_exempt
def print_document(request):
    """Función mejorada para imprimir documentos con manejo correcto de excepciones"""
    print("Solicitud de impresión recibida")
    if request.method != 'POST':
        return HttpResponseBadRequest("Método no permitido.")

    # Leer datos JSON del body
    try:
        data = json.loads(request.body)
        printer_name = data.get('printer_name')
        document_content = data.get('document_content')
        paper_size = data.get('paper_size', 'A4')
        copies = int(data.get('copies', 1))
        quality = data.get('quality', 'high')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error al leer los datos JSON.'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'Valor numérico inválido.'}, status=400)

    # Verificar que los datos esenciales estén presentes
    if not printer_name or not document_content:
        return JsonResponse({'error': 'Nombre de impresora y contenido del documento son obligatorios.'}, status=400)

    try:
        # Verificar si el documento es una imagen en base64
        is_image = False
        image_data = None
        
        if document_content.startswith('data:image'):
            is_image = True
            # Extraer los datos de la imagen
            header, encoded = document_content.split(",", 1)
            image_data = base64.b64decode(encoded)
        
        # Abrir la impresora seleccionada
        printer_handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(printer_handle, 2)

        # Configurar tamaño de papel - USAR CONSTANTES ESTÁNDAR
        devmode = printer_info["pDevMode"]
        
        # Definir códigos estándar para tamaños de papel comunes
        # Estas constantes están definidas en win32con
        PAPER_SIZES = {
            '10x15': 1,    # Usar tamaño personalizado 
            '13x18': 1,    # Usar tamaño personalizado
            '15x20': 1,    # Usar tamaño personalizado
            '20x25': 1,    # Usar tamaño personalizado
            'A4': win32con.DMPAPER_A4,
            'Letter': win32con.DMPAPER_LETTER
        }
        
        # Aplicar tamaño de papel si está disponible
        if paper_size in PAPER_SIZES:
            devmode.PaperSize = PAPER_SIZES[paper_size]
            
            # Si es tamaño personalizado (valor 1), también configurar dimensiones físicas
            if PAPER_SIZES[paper_size] == 1:
                # Extraer dimensiones del string (formato '10x15')
                if 'x' in paper_size:
                    try:
                        width_cm, height_cm = paper_size.split('x')
                        width_mm = int(float(width_cm) * 10)  # cm a mm
                        height_mm = int(float(height_cm) * 10)  # cm a mm
                        
                        # Solo configurar si los campos están disponibles
                        if hasattr(devmode, 'PaperWidth') and hasattr(devmode, 'PaperLength'):
                            devmode.PaperWidth = width_mm * 10  # mm a 0.1mm (unidad de DEVMODE)
                            devmode.PaperLength = height_mm * 10  # mm a 0.1mm (unidad de DEVMODE)
                    except:
                        pass  # Si hay error, usar los valores por defecto
        else:
            # Usar A4 como tamaño por defecto
            devmode.PaperSize = win32con.DMPAPER_A4
        
        # Configurar calidad de impresión
        quality_settings = {
            'draft': -1,    # Calidad borrador
            'normal': 0,    # Calidad normal
            'high': 1       # Alta calidad
        }
        
        if quality in quality_settings:
            devmode.PrintQuality = quality_settings[quality]
        
        # Configurar número de copias
        devmode.Copies = copies
        
        # Aplicar configuración al controlador de impresora
        win32print.SetPrinter(printer_handle, 2, printer_info, 0)
        
        # Crear el contexto de impresión
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        
        if is_image:
            # Imprimir imagen
            try:
                # Crear un archivo temporal para la imagen
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(image_data)
                temp_file.close()
                
                # Abrir la imagen con PIL
                img = Image.open(temp_file.name)
                
                # Iniciar el documento
                hdc.StartDoc('Collage Photobooth')
                hdc.StartPage()
                
                # Obtener dimensiones de la página
                dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
                dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY)
                page_width = hdc.GetDeviceCaps(win32con.PHYSICALWIDTH)
                page_height = hdc.GetDeviceCaps(win32con.PHYSICALHEIGHT)
                
                # Calcular dimensiones para mantener proporción
                img_ratio = img.width / img.height
                page_ratio = page_width / page_height
                
                if img_ratio > page_ratio:
                    # Imagen más ancha que alta en proporción
                    target_width = page_width
                    target_height = int(page_width / img_ratio)
                else:
                    # Imagen más alta que ancha en proporción
                    target_height = page_height
                    target_width = int(page_height * img_ratio)
                
                # Calcular posición para centrar la imagen
                pos_x = (page_width - target_width) // 2
                pos_y = (page_height - target_height) // 2
                
                # Convertir la imagen a formato de mapa de bits compatible con Windows
                dib = ImageWin.Dib(img)
                
                # Dibujar la imagen en el contexto de la impresora
                dib.draw(hdc.GetHandleOutput(), (pos_x, pos_y, pos_x + target_width, pos_y + target_height))
                
                # Finalizar la página y el documento
                hdc.EndPage()
                hdc.EndDoc()
                
                # Eliminar el archivo temporal
                os.unlink(temp_file.name)
                
            except Exception as img_error:
                # Si falla la impresión de imagen, intentar imprimir como texto
                print(f"Error al imprimir imagen: {str(img_error)}")
                
                # Intentar limpiar recursos si ya se iniciaron
                try:
                    if 'hdc' in locals() and hdc:
                        try:
                            if hasattr(hdc, 'AbortDoc'):
                                hdc.AbortDoc()
                            hdc.DeleteDC()
                        except:
                            pass
                    
                    if 'printer_handle' in locals() and printer_handle:
                        try:
                            win32print.ClosePrinter(printer_handle)
                        except:
                            pass
                    
                    if 'temp_file' in locals() and temp_file and os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
                except:
                    pass
                
                return JsonResponse({'error': f'Error al imprimir imagen: {str(img_error)}'}, status=500)
        else:
            # Imprimir documento de texto
            hdc.StartDoc('Documento Django')
            hdc.StartPage()
            
            # Ajustar fuente y formato para imprimir
            hdc.SetMapMode(win32con.MM_TWIPS)  # 1/1440 pulgadas
            
            # Crear fuente para el texto
            font = win32ui.CreateFont({
                'name': 'Arial',
                'height': 36,  # Tamaño de fuente
                'weight': 400  # Normal
            })
            
            hdc.SelectObject(font)
            
            # Posición inicial (1 pulgada desde borde superior e izquierdo)
            x = 1440  # 1 pulgada en twips
            y = 1440  # 1 pulgada en twips
            
            # Dividir el texto en líneas
            lines = document_content.split('\n')
            
            for line in lines:
                if line.strip():  # No imprimir líneas vacías
                    hdc.TextOut(x, y, line)
                    y += 300  # Espacio entre líneas
            
            hdc.EndPage()
            hdc.EndDoc()

        # Limpiar recursos
        hdc.DeleteDC()
        win32print.ClosePrinter(printer_handle)

        return JsonResponse({'success': True, 'message': 'Documento enviado a impresión correctamente.'})

    # Cambiar esto:
    # except win32print.error as e:
    #     return JsonResponse({'error': f'Error de impresión: {str(e)}'}, status=500)
    
    # Por esto (manejo general de excepciones):
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # Intentar limpiar recursos si ya se iniciaron
        try:
            if 'hdc' in locals() and hdc:
                try:
                    if hasattr(hdc, 'AbortDoc'):
                        hdc.AbortDoc()
                    hdc.DeleteDC()
                except:
                    pass
            
            if 'printer_handle' in locals() and printer_handle:
                try:
                    win32print.ClosePrinter(printer_handle)
                except:
                    pass
            
            if is_image and 'temp_file' in locals() and temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
        except:
            pass
        
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)
    
def check_print_spooler():
    """Verifica el estado del servicio de cola de impresión y lo reinicia si es necesario"""
    try:
        import subprocess
        
        # Verificar el estado del servicio
        result = subprocess.run(['sc', 'query', 'Spooler'], capture_output=True, text=True)
        
        if 'RUNNING' not in result.stdout:
            # El servicio no está corriendo, intentar reiniciarlo
            logger.warning("El servicio Print Spooler no está en ejecución. Intentando reiniciar...")
            restart = subprocess.run(['sc', 'start', 'Spooler'], capture_output=True, text=True)
            
            # Esperar un momento para que se inicie
            import time
            time.sleep(5)
            
            # Verificar de nuevo
            result = subprocess.run(['sc', 'query', 'Spooler'], capture_output=True, text=True)
            if 'RUNNING' in result.stdout:
                logger.info("Servicio Print Spooler reiniciado exitosamente")
                return True
            else:
                logger.error("No se pudo reiniciar el servicio Print Spooler")
                return False
        else:
            logger.info("Servicio Print Spooler funcionando correctamente")
            return True
            
    except Exception as e:
        logger.error(f"Error al verificar servicio Print Spooler: {str(e)}")
        return False

@csrf_exempt
@require_POST
def send_whatsapp(request):
    if not request.user.is_authenticated:
        return redirect("login")
    """Enviar collage por WhatsApp"""
    try:
        data = json.loads(request.body)
        collage_id = data.get('collage_id')
        phone = data.get('phone')
        message = data.get('message', '')
        
        if not all([collage_id, phone]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        collage = get_object_or_404(CollageResult, collage_id=collage_id)
        
        # Aquí iría el código para integrar con la API de WhatsApp
        # Por ahora solo actualizamos el contador
        
        collage.share_count += 1
        collage.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error al enviar por WhatsApp: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})
    success_message = ("Evento eliminado exitosamente")
    



def launch_photobooth(request, evento_id):
    """Vista principal que inicia el flujo del photobooth"""
    evento = get_object_or_404(Evento, pk=evento_id)
    
    # Obtener la configuración del photobooth
    try:
        config = PhotoboothConfig.objects.get(evento=evento)
    except PhotoboothConfig.DoesNotExist:
        return render(request, 'photobooth/error.html', {
            'mensaje': 'No hay configuración para el photobooth. Por favor configúrela primero.'
        })
    
    # Obtener la plantilla seleccionada
    template = None
    template_json = '{}'
    if config.plantilla_collage:
        template = config.plantilla_collage
        try:
            template_data = json.loads(template.template_data)
            template_json = json.dumps(template_data)
        except:
            template_json = '{}'
    else:
        return render(request, 'photobooth/error.html', {
            'mensaje': 'No hay plantilla de collage seleccionada. Por favor seleccione una plantilla.'
        })
    
    # Crear una nueva sesión para esta sesión de photobooth
    session = CollageSession.objects.create(
        evento=evento,
        template=template,
        session_id=str(uuid.uuid4()),
        status='active'
    )
    
    return render(request, 'photobooth/session.html', {
        'evento': evento,
        'config': config,
        'template': template,
        'template_json': template_json,
        'session_id': session.session_id,
        'return_url': request.META.get('HTTP_REFERER', f'/eventos/{evento_id}/')
    })


def session_result(request, session_id):
    """Muestra el resultado de una sesión de photobooth"""
    session = get_object_or_404(CollageSession, session_id=session_id)
    evento = session.evento
    template = session.template
    
    # Obtener todas las fotos de la sesión
    photos = SessionPhoto.objects.filter(session=session).order_by('frame_index')
    
    # Determinar si la sesión está completa
    template_data = json.loads(template.template_data) if template.template_data else {'frames': []}
    total_frames = len(template_data.get('frames', []))
    is_complete = photos.count() == total_frames
    
    # Obtener o crear el resultado del collage si está completo
    collage_result = None
    remaining_frames = []
    
    if is_complete:
        # Buscar un resultado existente o crear uno nuevo
        collage_result, created = CollageResult.objects.get_or_create(
            session=session,
            defaults={
                'collage_id': str(uuid.uuid4()),
                'print_count': 0
            }
        )
        
        # Si es creado, generar la imagen del collage
        if created:
            # Aquí iría el código para generar la imagen del collage
            # Este paso depende de cómo esté implementada la generación del collage
            pass
    else:
        # Calcular marcos restantes
        remaining_frames = range(total_frames - photos.count())
    
    return render(request, 'collage/session_result.html', {
        'evento': evento,
        'template': template,
        'photos': photos,
        'is_complete': is_complete,
        'collage_result': collage_result,
        'remaining_frames': remaining_frames,
        'session_id': session_id
    })

@csrf_exempt
def update_print_count(request):
    """Actualiza el contador de impresiones de un collage"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        collage_id = data.get('collage_id')
        
        if not collage_id:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Obtener el collage
        collage = get_object_or_404(CollageResult, collage_id=collage_id)
        
        # Incrementar contador
        collage.print_count += 1
        collage.save()
        
        return JsonResponse({'success': True, 'print_count': collage.print_count})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    return render(request, "register/register.html", {"form": form})

def verificar_usuario(request):
    username = request.GET.get("username", "").strip()

    if not username:  # 📌 Si no se envió un usuario, devolver error JSON
        return JsonResponse({"error": "No se proporcionó un nombre de usuario"}, status=400)

    existe = User.objects.filter(username=username).exists()
    
    return JsonResponse({"existe": existe})  # 📌 Devuelve JSON válido

def verificar_email(request):
    email = request.GET.get("email", "").strip()

    if not email:  # 📌 Si no se proporciona un email, devolver un error
        return JsonResponse({"error": "No se proporcionó un email"}, status=400)

    existe = User.objects.filter(email=email).exists()
    return JsonResponse({"existe": existe})  # 📌 Devuelve `true` si el email ya está registrado


def descargar_foto(request, evento_id): #Función para retornar vista de fotografías de un evento
    if not request.user.is_authenticated:  #Si el usuario no está autenticado....
        return redirect("login") #Redirigir al login

    evento=Evento.objects.get(id=evento_id) #Obtener un evento en específico
 
    imagenes=evento.fotografias.all()  #Obtener todas las fotografías de un evento
    return render(request,"fotografias/descargar_foto.html",{
        "evento":evento,
        "imagenes":imagenes,
        
         
    })

def mis_eventos(request):  #Función para retornar vista de los eventos de un cliente
    if not request.user.is_authenticated:  #Si el usuario no está autenticado...
        return redirect("login") #Redirigir al login
    
    cliente = Cliente.objects.get(usuario=request.user)   #Obtener un cliente mediante el usuario por medio del ORM
    evento = Evento.objects.filter(cliente=cliente).first() #Obtener el primer evento
    imagenes=evento.fotografias.all() #Obtener todas las fotografías del evento
    return render(request,"fotografias/descargar_foto.html",{
        "evento":evento,
        "imagenes":imagenes
       
    })

#Mostrar las fotos guardadas
def lista_fotos(request):
    fotos = Fotografia.objects.all()
    return render(request, "fotografias/foto_list.html", {"fotografias": fotos})

# Subir fotos de los eventos
def subir_foto(request):
    if request.method == "POST":
        form = AñadirFotoForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)  # 📌 No guarda en la base de datos aún
            foto.usuario = request.user  # 📌 Asigna el usuario autenticado

            # 📌 Si el formulario no tiene evento, asignar un evento por defecto
            if not foto.evento:
                foto.evento = Evento.objects.first()  # O elegir un evento válido

            foto.save()  # 📌 Ahora sí guarda la foto
            return redirect("lista_fotos")
        else:
            print("Errores en el formulario:", form.errors)

    else:
        form = AñadirFotoForm()

    return render(request, "fotografias/subir_foto.html", {"form": form})

#Envío de las fotos a facebook
def publicar_foto_facebook(request, foto_id):
    foto = get_object_or_404(Fotografia, id=foto_id)
    page_id = settings.FACEBOOK_PAGE_ID  # 📌 Obtiene el Page ID desde settings.py
    access_token = settings.FACEBOOK_ACCESS_TOKEN  # 📌 Obtiene el Token de Página

    # Reemplazar la URL local con la de ngrok
    imagen_url = request.build_absolute_uri(foto.img.url).replace(
        "http://127.0.0.1:8000", "https://55dc-191-156-43-126.ngrok-free.app"
    )

    # TEST: Verificar accesibilidad de la imagen antes de publicar en Facebook
    import requests
    try:
        test_response = requests.get(imagen_url)
        print("[TEST] Status de acceso a la imagen:", test_response.status_code)
        if test_response.status_code != 200:
            print("[TEST] Contenido recibido:", test_response.content[:200])
    except Exception as e:
        print("[TEST] Error accediendo a la imagen:", e)

    print("[TEST] URL enviada a Facebook:", imagen_url)

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


def añadir_foto(request, evento_id): #Función que retorna el formulario para añadir una foto a un evento
    if not request.user.is_authenticated: #Si el usuario no está autenticado...
        return redirect("login") #Redirigir al login
    
    if  not request.user.is_superuser:  #Si no es un superusuario...
     return HttpResponse("No estás autorizado para acceder a esta página") #Retornar mensaje de error
    evento=Evento.objects.get(id=evento_id) #Obtener un evento en específico
    
    if request.method=="POST": #Si la petición es POST
        form=AñadirFotoForm(request.POST, request.FILES) #Llamar al formulario
        archivos = request.FILES.getlist('img')
       

        if form.is_valid(): #Si el formulario es válido obtener los datos
            descripcion=form.cleaned_data["descripcion"]
            
            for imagen in archivos:
               
                
                 fotografia=Fotografia.objects.create(descripcion=descripcion, img=imagen, evento=evento)#Crear un objeto de Fotografia
                 fotografia.save() #Guardar objeto
            return redirect(reverse("descargar_foto", kwargs={"evento_id":evento_id})) #Redirigir al la vista "descargar_foto"
            
        else: #Retornar el formulario si no fue válido mostrando el error
            return render(request,"añadir_fotos/formulario.html",{
                "form":form
            })
        
    
    return render(request,"añadir_fotos/formulario.html",{
        "evento":evento,
        "form":AñadirFotoForm()
    })




# Variables globales
camera = None
camera_running = False
last_frame = None
output_folder = os.path.join('camara', 'static', 'images')
current_camera_index = 0

camera_settings = {
    'iso': 100,
    'iso_min': 100,
    'iso_max': 1600
}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

def get_available_cameras(max_to_check=10):
    available_cameras = []
    for i in range(max_to_check):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            camera_name = f"Cámara {i}"
            available_cameras.append({"index": i, "name": camera_name})
            cap.release()
    return available_cameras

def get_camera(camera_index=None):
    global camera, current_camera_index

    if camera_index is not None:
        current_camera_index = int(camera_index)

    if camera is not None:
        camera.release()
        camera = None

    camera = cv2.VideoCapture(current_camera_index)
    if not camera.isOpened():
        print(f"Error: No se pudo abrir la cámara con índice {current_camera_index}")
        return None

    apply_camera_settings()
    return camera

def apply_camera_settings():
    global camera, camera_settings

    if camera is None or not camera.isOpened():
        return

    try:
        camera.set(cv2.CAP_PROP_ISO_SPEED, camera_settings['iso'])

        base_iso = camera_settings['iso_min']
        current_iso = camera_settings['iso']
        exposure_factor = base_iso / current_iso

        current_exposure = camera.get(cv2.CAP_PROP_EXPOSURE)
        if current_exposure != 0:
            camera.set(cv2.CAP_PROP_EXPOSURE, current_exposure * exposure_factor)

        print(f"ISO configurado a: {camera_settings['iso']}")
    except Exception as e:
        print(f"Error al configurar ISO: {e}")

@csrf_exempt
def set_white_balance(request):
    global camera

    if camera is None or not camera.isOpened():
        return JsonResponse({'error': 'La cámara no está activa.'}, status=400)

    try:
        data = json.loads(request.body)
        wb_mode = data.get('white_balance')

        # Modo manual según el modo seleccionado (esto varía por cámara)
        wb_values = {
            'auto': 0,
            'daylight': 1,
            'cloudy': 2,
            'shade': 3,
            'tungsten': 4,
            'fluorescent': 5,
            'incandescente': 6
        }

        # CAP_PROP_WHITE_BALANCE_BLUE_U está deprecated en algunas versiones, usar 44 como ID numérico si es necesario
        if wb_mode in wb_values:
            camera.set(cv2.CAP_PROP_AUTO_WB, 0)  # Desactiva el auto WB
            # No todas las cámaras aceptan este valor. Esto depende del driver:
            camera.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, wb_values[wb_mode])
            return JsonResponse({'message': f'Balance de blancos ajustado a {wb_mode}'})
        else:
            return JsonResponse({'error': 'Modo no válido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def generate_frames():
    global camera_running, last_frame
    camera_running = True
    cam = get_camera()

    if cam is None:
        return

    while camera_running:
        success, frame = cam.read()
        if not success:
            break

        last_frame = frame.copy()
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

def camaras(request):
    images = []
    if os.path.exists(output_folder):
        images = [f for f in os.listdir(output_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
        images.sort(reverse=True)

    available_cameras = get_available_cameras()

    return render(request, 'camaras/camaras.html', {
        'images': images,
        'cameras': available_cameras,
        'current_camera': current_camera_index,
        'camera_settings': camera_settings
    })

@csrf_exempt
def capture(request):
    global last_frame, output_folder

    if request.method == 'POST':
        if last_frame is not None:
            try:
                filename = f"captura_{uuid.uuid4().hex}.jpg"
                image_path = os.path.join(output_folder, filename)
                cv2.imwrite(image_path, last_frame)

                return JsonResponse({
                    'success': True,
                    'image_path': f"/static/images/{filename}"
                })

            except Exception as e:
                print("Error al guardar la imagen:", e)
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'No hay imagen para capturar.'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def set_iso(request):
    global camera_settings

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_iso = int(data.get('iso', 100))

            if camera_settings['iso_min'] <= new_iso <= camera_settings['iso_max']:
                camera_settings['iso'] = new_iso
                apply_camera_settings()
                return JsonResponse({
                    'success': True,
                    'iso': new_iso,
                    'message': f'ISO actualizado a {new_iso}'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'El valor del ISO está fuera del rango permitido.'
                })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def switch_camera(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            camera_index = int(data.get('camera_index', 0))
            get_camera(camera_index)  # Esto reinicia la cámara con el nuevo índice

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})



def video_feed(request):
    return StreamingHttpResponse(generate_frames(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

# funciones para la impresora
def get_available_printers():
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    return printers

def list_printers(request):
    printers = get_available_printers()
    return JsonResponse({'printers': printers})

def impresoras(request, evento_id):
    eventos=Evento.objects.get(id=evento_id)  # Obtener el evento
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return render(request, 'impresoras/impresoras.html',{
            "printers":printers,
            "eventos":eventos
        })
    except Exception as e:
        return render(request, 'impresoras/impresoras.html', {'error': str(e)})

# @csrf_exempt
# def print_document(request):
#     print("solicitud de impresión recibida")
#     if request.method != 'POST':
#         return HttpResponseBadRequest("Método no permitido.")

#     # Leer datos JSON del body
#     try:
#         data = json.loads(request.body)
#         printer_name = data.get('printer_name')
#         document_content = data.get('document_content')
#         paper_size = data.get('paper_size', 'A4')
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Error al leer los datos JSON.'}, status=400)

#     # Verificar que los datos esenciales estén presentes
#     if not printer_name or not document_content:
#         return JsonResponse({'error': 'Nombre de impresora y contenido del documento son obligatorios.'}, status=400)

#     try:
#         # Abrir la impresora seleccionada
#         printer_handle = win32print.OpenPrinter(printer_name)
#         printer_info = win32print.GetPrinter(printer_handle, 2)

#         # Crear el contexto de impresión
#         hprinter = win32ui.CreateDC()
#         hprinter.CreatePrinterDC(printer_name)
#         hprinter.StartDoc('Documento Django')
#         hprinter.StartPage()

#         # Ajustar fuente y formato para imprimir
#         hprinter.TextOut(100, 100, document_content)  # Ajusta las coordenadas y el contenido del texto
#         hprinter.EndPage()
#         hprinter.EndDoc()

#         hprinter.DeleteDC()
#         win32print.ClosePrinter(printer_handle)

#         return JsonResponse({'message': 'Documento enviado a impresión correctamente.'})

#     except win32print.error as e:
#         return JsonResponse({'error': f'Error de impresión: {str(e)}'}, status=500)

#     except Exception as e:
#         return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)

@csrf_exempt
def list_printers(request):
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return JsonResponse({'printers': printers})
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener las impresoras: {str(e)}'}, status=500)

@csrf_exempt
@require_POST
def save_collage(request):
    """API para guardar un collage generado en el frontend"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        image_data = data.get('image_data')
        
        logger.info(f"Recibida solicitud para guardar collage. Session ID: {session_id}")
        
        if not session_id or not image_data:
            logger.error("Datos incompletos en solicitud save_collage")
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Usar CollageSession directamente
        try:
            session = CollageSession.objects.get(session_id=session_id)
        except CollageSession.DoesNotExist:
            return JsonResponse({'success': False, 'error': f'Sesión con ID {session_id} no encontrada'})
        
        # Procesar la imagen base64
        if image_data.startswith('data:image'):
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            decoded_image = base64.b64decode(imgstr)
            
            # Generar un ID único para el collage
            collage_id = str(uuid.uuid4())
            
            # Verificar si ya existe un resultado para esta sesión
            existing_collage = CollageResult.objects.filter(session=session).first()
            if existing_collage:
                logger.info(f"Actualizando collage existente: {existing_collage.collage_id}")
                # Si ya existe, actualizar su imagen
                collage_result = existing_collage
                collage_result.collage_id = collage_id
            else:
                logger.info(f"Creando nuevo registro de collage con ID: {collage_id}")
                # Crear un nuevo registro de collage
                collage_result = CollageResult(
                    collage_id=collage_id,
                    session=session
                )
            
            # Asegurar que existe el directorio destino
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'collage', 'results')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Guardar la imagen en la ubicación especificada
            filename = f"collage_{collage_id}.{ext}"
            filepath = os.path.join(upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(decoded_image)
            
            # Actualizar el modelo con la ruta relativa
            relative_path = os.path.join('collage', 'results', filename)
            collage_result.image = relative_path
            collage_result.save()
            
            logger.info(f"Imagen guardada como: {filename}")
            
            # Cambiar estado de la sesión
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
            logger.info(f"Sesión marcada como completada")
            
            # Actualizar estadísticas
            try:
                config = PhotoboothConfig.objects.get(evento=session.evento)
                config.total_sesiones += 1
                photos_count = SessionPhoto.objects.filter(session=session).count()
                config.total_fotos += photos_count
                config.save()
                logger.info(f"Estadísticas actualizadas: {photos_count} fotos en sesión")
            except Exception as stats_error:
                logger.warning(f"No se pudieron actualizar estadísticas: {str(stats_error)}")
            
            # Construir URL completa para la respuesta
            image_url = f"{settings.MEDIA_URL}{relative_path}"
            
            return JsonResponse({
                'success': True, 
                'collage_id': collage_id,
                'image_url': image_url
            })
        else:
            logger.error("Formato de imagen no válido en save_collage")
            return JsonResponse({'success': False, 'error': 'Formato de imagen no válido'})
        
    except Exception as e:
        logger.error(f"Error al guardar collage: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})



    

def galeria_quinces(request):
    return render(request, 'index/galerias/quinces.html')

def galeria_bodas(request):
    return render(request, 'index/galerias/bodas.html')

def galeria_otros(request):
    return render(request, 'index/galerias/otros.html')

@csrf_exempt
def latest_collage(request):
    """
    API endpoint para obtener el collage más reciente
    Utilizado por la aplicación móvil para sincronizarse
    """
    try:
        # Obtener el último collage creado
        latest = CollageResult.objects.order_by('-created_at').first()
        
        # Si no hay collages, devolver error
        if not latest:
            return JsonResponse({
                'success': False,
                'error': 'No hay collages disponibles'
            })
            
        # Construir la URL completa de la imagen
        image_url = request.build_absolute_uri(latest.image.url)
        
        # Obtener información del evento para contexto
        evento = latest.session.evento
        client_name = f"{evento.cliente.nombre} {evento.cliente.apellido}" if evento.cliente else "Cliente"
        event_name = evento.nombre
        
        # Devolver datos del collage
        return JsonResponse({
            'success': True,
            'collage_id': latest.collage_id,
            'image_url': image_url,
            'created_at': latest.created_at.isoformat(),
            'event_name': event_name,
            'client_name': client_name
        })
        
    except Exception as e:
        logger.error(f"Error en latest_collage: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': str(e)
        })

@csrf_exempt
@require_POST
def update_share_count(request):
    """
    API endpoint para actualizar el contador de comparticiones
    Llamado por la aplicación móvil cuando se comparte un collage
    """
    try:
        # Leer datos del request
        data = json.loads(request.body)
        collage_id = data.get('collage_id')
        
        if not collage_id:
            return JsonResponse({
                'success': False,
                'error': 'Collage ID no proporcionado'
            })
        
        # Buscar el collage
        collage = get_object_or_404(CollageResult, collage_id=collage_id)
        
        # Incrementar contador
        collage.share_count += 1
        collage.save()
        
        return JsonResponse({
            'success': True,
            'share_count': collage.share_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Formato JSON inválido'
        }, status=400)
        
    except CollageResult.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Collage no encontrado'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error en update_share_count: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def api_session_photos(request):
    """
    API para obtener las fotos individuales y el collage de una sesión de photobooth.
    Recibe el session_id por GET o POST y responde con las URLs de las fotos y el collage.
    """
    session_id = request.GET.get('session_id') or request.POST.get('session_id')
    if not session_id:
        return JsonResponse({'success': False, 'error': 'session_id es requerido'}, status=400)

    session = CollageSession.objects.filter(session_id=session_id).first()
    if not session:
        return JsonResponse({'success': False, 'error': 'Sesión no encontrada'}, status=404)

    # Obtener fotos individuales
    photos = SessionPhoto.objects.filter(session=session).order_by('frame_index')
    photo_urls = [request.build_absolute_uri(photo.image.url) for photo in photos if photo.image]

    # Obtener collage
    collage_result = CollageResult.objects.filter(session=session).first()
    collage_url = request.build_absolute_uri(collage_result.image.url) if collage_result and collage_result.image else None

    return JsonResponse({
        'success': True,
        'photos': photo_urls,
        'collage': collage_url
    })
