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
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.contrib import messages
from .models import *
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
import json
import uuid
import base64
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import logging
from django.contrib.auth.views import PasswordResetView
logger = logging.getLogger(__name__)
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.shortcuts import render
import cv2
import time
import win32print
import win32ui




class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    



def index(request):  #Función  para retornar vista principal
    return render(request, "index/index.html")


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
        return render(request, "fotografias/eventos_cliente.html", {
            "mensaje": mensaje
        })
    
    lista_eventos = cliente.eventos.all()  #Obtener todos los eventos de un cliente específico

    if not lista_eventos.exists():   #Si no existe ningún evento asociado, retornar mensaje
        return render(request, "fotografias/eventos_cliente.html", {
            "mensaje": "No tiene eventos actualmente"
        })
    
    # --- FILTRO POR BÚSQUEDA ---
    query = request.GET.get('q')
    if query:
        lista_eventos = lista_eventos.filter(
            Q(nombre__icontains=query)
        )

    # --- ORDENAMIENTO ---
    orden = request.GET.get('orden')
    if orden == 'nombre':
        lista_eventos = lista_eventos.order_by('nombre')
    elif orden == 'nombre_desc':
        lista_eventos = lista_eventos.order_by('-nombre')
    elif orden == 'cliente':
        lista_eventos = lista_eventos.order_by('cliente__nombre')
    elif orden == 'cliente_desc':
        lista_eventos = lista_eventos.order_by('-cliente__nombre')
    elif orden == 'fecha_hora':
        lista_eventos = lista_eventos.order_by('fecha_hora')
    elif orden == 'fecha_hora_desc':
        lista_eventos = lista_eventos.order_by('-fecha_hora')

    # Evento e imágenes para vista previa (por ejemplo, el primero)
    evento = lista_eventos.first()
    imagenes = evento.fotografias.all() if evento else []
    
    #Retornar vista con respectivos contextos

    return render(request, "fotografias/eventos_cliente.html", {
        "evento": evento,
        "imagenes": imagenes,
        "lista_eventos": lista_eventos
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
        form = FotografiaForm(request.POST, request.FILES)
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
        form = FotografiaForm()

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
            "http://127.0.0.1:8000", "https://e8ee-191-156-33-165.ngrok-free.app "
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
        "http://127.0.0.1:8000", "https://e8ee-191-156-33-165.ngrok-free.app "
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
            
            # Si no hay resultados con la búsqueda de texto completo, intentamos con LIKE
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
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para configurar el photobooth de un evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    config, created = PhotoboothConfig.objects.get_or_create(evento=evento)
    
    # Inicializar form como None para evitar el UnboundLocalError
    form = None
    
    template_id = request.GET.get('template')
    
    if request.method == 'POST':
        # Imprimir valores del POST para depuración
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
                
            # Evitar error si los campos no existen aún en la BD
            try:
                # Guardar configuración de resolución y balance de blancos
                resolucion = request.POST.get('resolucion_camara')
                if resolucion:
                    config.resolucion_camara = resolucion
                    print(f"Guardando resolución: {resolucion}")
                    
                balance = request.POST.get('balance_blancos')
                if balance:
                    config.balance_blancos = balance
                    print(f"Guardando balance de blancos: {balance}")
            except AttributeError:
                print("Advertencia: Los campos resolucion_camara o balance_blancos no existen aún en la base de datos")

            # Verificación explícita del campo de imagen
            if 'imagen_fondo' in request.FILES:
                config.imagen_fondo = request.FILES['imagen_fondo']
                print("Guardando imagen:", request.FILES['imagen_fondo'])
            
            config.save()

            form.save_m2m()  # Para relaciones ManyToMany
            messages.success(request, "Configuración guardada correctamente")
            return redirect('evento_detail', pk=evento.id)
        else:
            print("Errores del formulario:", form.errors)
    else:
        # En caso de GET
        form = PhotoboothConfigForm(instance=config, evento=evento)
        
        # Si hay un template_id en la URL y no es un POST, actualizamos el valor inicial
        if template_id and not form.is_bound:
            try:
                template = CollageTemplate.objects.get(template_id=template_id, evento=evento)
                form.initial['plantilla_collage'] = template.template_id
                
                # También actualizamos el objeto config temporalmente para la vista previa
                if config is None:
                    config = PhotoboothConfig(evento=evento)
                config.plantilla_collage = template
            except CollageTemplate.DoesNotExist:
                pass
    
    # Para la vista previa del collage
    selected_template = config.plantilla_collage
    frames = []
    if selected_template:
        frames = selected_template.get_frames()
    
    # Asegúrate de que form esté definido antes de pasarlo al contexto
    if form is None:
        form = PhotoboothConfigForm(instance=config, evento=evento)
    
    # Evitar error si los campos no existen aún
    try:
        print(f"Configuración actual: Resolución={config.resolucion_camara}, Balance={config.balance_blancos}")
    except AttributeError:
        print("Advertencia: Los campos resolucion_camara o balance_blancos no existen aún en la base de datos")
    
    context = {
        'evento': evento,
        'form': form,
        'config': config,
        'selected_template': selected_template,
        'frames': frames
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
    
    context = {
        'evento': evento,
        'config': config
    }
    
    return render(request, 'photobooth/launch_photobooth.html', context)

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
    if not request.user.is_authenticated:
        return redirect("login")
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
            image_data = ContentFile(base64.b64decode(imgstr), name=f"{template_id}_bg.{ext}")
            template.background_image = image_data
        
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
    session = PhotoboothSession.objects.create(
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
    if not request.user.is_authenticated:
        return redirect("login")
    """API para guardar una foto tomada durante la sesión"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        frame_index = data.get('frame_index')
        image_data = data.get('image_data')
        
        if not all([session_id, image_data, frame_index is not None]):
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Obtener la sesión
        session = get_object_or_404(CollageSession, session_id=session_id)
        
        # Procesar la imagen base64
        if ',' in image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            decoded_image = base64.b64decode(imgstr)
            
            # Generar nombre de archivo único
            filename = f"session_{session_id}_frame_{frame_index}.{ext}"
            
            # Guardar imagen
            photo = SessionPhoto(session=session, frame_index=frame_index)
            photo.image.save(filename, ContentFile(decoded_image), save=True)
            
            return JsonResponse({'success': True, 'photo_id': photo.id})
        else:
            return JsonResponse({'success': False, 'error': 'Formato de imagen no válido'})
        
    except Exception as e:
        logger.error(f"Error al guardar foto de sesión: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def session_result(request, session_id):
    if not request.user.is_authenticated:
        return redirect("login")
    """Vista para mostrar el resultado de una sesión de fotos"""
    session = get_object_or_404(CollageSession, session_id=session_id)
    template = session.template
    evento = session.evento
    
    # Obtener todas las fotos tomadas en esta sesión
    photos = SessionPhoto.objects.filter(session=session).order_by('frame_index')
    
    # Verificar si se completaron todas las fotos
    template_data = json.loads(template.template_data)
    frames = template_data.get('frames', [])
    total_frames = len(frames)
    is_complete = photos.count() == total_frames
    
    # Si la sesión está completa, generar/obtener el collage final
    collage_result = None
    if is_complete:
        collage_result = CollageResult.objects.filter(session=session).first()
        if not collage_result and session.status == 'active':
            # Generar el collage si no existe
            collage_result = generate_collage(session, template_data, photos, frames)
            
            # Actualizar estado de la sesión
            session.status = 'completed'
            session.completed_at = timezone.now()
            session.save()
    
    # Calcular marcos restantes para la vista
    remaining_count = total_frames - photos.count()
    remaining_frames = range(remaining_count)
    
    context = {
        'evento': evento,
        'session': session,
        'template': template,
        'photos': photos,
        'is_complete': is_complete,
        'collage_result': collage_result,
        'remaining_frames': remaining_frames
    }
    
    return render(request, 'collage/session_result.html', context)

def generate_collage(session, template_data, photos, frames):
    if not request.user.is_authenticated:
        return redirect("login")
    """Genera una imagen de collage a partir de una sesión completada"""
    try:
        # Dimensiones del collage (10x15 cm a 300dpi)
        width_px = int(10 * 118.11)  # 10cm a 300dpi
        height_px = int(15 * 118.11)  # 15cm a 300dpi
        
        # Crear imagen base
        background_color = template_data.get('backgroundColor', '#FFFFFF')
        if background_color.startswith('#'):
            r = int(background_color[1:3], 16)
            g = int(background_color[3:5], 16)
            b = int(background_color[5:7], 16)
            bg_color = (r, g, b, 255)
        else:
            bg_color = (255, 255, 255, 255)  # Blanco por defecto
        
        collage_img = Image.new('RGBA', (width_px, height_px), bg_color)
        
        # Si hay imagen de fondo, aplicarla
        if session.template.background_image:
            try:
                bg_img = Image.open(session.template.background_image.path)
                bg_img = bg_img.resize((width_px, height_px), Image.LANCZOS)
                # Mezclar con la imagen base
                collage_img = Image.alpha_composite(collage_img, bg_img.convert('RGBA'))
            except Exception as e:
                logger.error(f"Error al aplicar imagen de fondo: {str(e)}")
        
        # Colocar cada foto en su posición
        for photo in photos:
            frame = frames[photo.frame_index]
            
            # Convertir dimensiones relativas a píxeles
            frame_width = int(float(frame['width'].replace('px', '')))
            frame_height = int(float(frame['height'].replace('px', '')))
            frame_left = int(float(frame['left'].replace('px', '')))
            frame_top = int(float(frame['top'].replace('px', '')))
            
            # Escalar a dimensiones reales
            scale_factor = width_px / 378  # Factor entre px de pantalla y px de imagen (10cm a 300dpi / 10cm a 96dpi)
            frame_width = int(frame_width * scale_factor)
            frame_height = int(frame_height * scale_factor)
            frame_left = int(frame_left * scale_factor)
            frame_top = int(frame_top * scale_factor)
            
            # Abrir foto y redimensionar para que encaje en el marco
            photo_img = Image.open(photo.image.path)
            photo_img = photo_img.resize((frame_width, frame_height), Image.LANCZOS)
            
            # Pegar la foto en la posición correcta
            collage_img.paste(photo_img, (frame_left, frame_top))
        
        # Guardar el resultado
        collage_id = str(uuid.uuid4())
        img_io = io.BytesIO()
        collage_img.save(img_io, format='JPEG', quality=90)
        img_content = ContentFile(img_io.getvalue())
        
        # Crear registro en la base de datos
        collage_result = CollageResult(
            collage_id=collage_id,
            session=session
        )
        collage_result.image.save(f"collage_{collage_id}.jpg", img_content, save=True)
        
        return collage_result
        
    except Exception as e:
        logger.error(f"Error al generar collage: {str(e)}")
        return None

@csrf_exempt
@require_POST
def update_print_count(request):
    if not request.user.is_authenticated:
        return redirect("login")
    """Actualizar el contador de impresiones de un collage"""
    try:
        data = json.loads(request.body)
        collage_id = data.get('collage_id')
        
        if not collage_id:
            return JsonResponse({'success': False, 'error': 'ID de collage no proporcionado'})
        
        collage = get_object_or_404(CollageResult, collage_id=collage_id)
        collage.print_count += 1
        collage.save()
        
        return JsonResponse({'success': True, 'print_count': collage.print_count})
        
    except Exception as e:
        logger.error(f"Error al actualizar contador de impresiones: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

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
    

def añadir_foto(request, evento_id): #Función que retorna el formulario para añadir una foto a un evento
    if not request.user.is_authenticated: #Si el usuario no está autenticado...
        return redirect("login") #Redirigir al login
    
    if  not request.user.is_superuser:  #Si no es un superusuario...
     return HttpResponse("No estás autorizado para acceder a esta página") #Retornar mensaje de error
    evento=Evento.objects.get(id=evento_id) #Obtener un evento en específico
    
    if request.method=="POST": #Si la petición es POST
        form=FotografiaForm(request.POST, request.FILES) #Llamar al formulario
        if form.is_valid(): #Si el formulario es válido obtener los datos
            descripcion=form.cleaned_data["descripcion"]
            img=form.cleaned_data["img"]
            invitado=form.cleaned_data["invitado"]
            fotografia=Fotografia.objects.create(descripcion=descripcion, img=img, evento=evento, invitado=invitado)#Crear un objeto de Fotografia
            fotografia.save() #Guardar objeto
            return redirect(reverse("descargar_foto", kwargs={"evento_id":evento_id})) #Redirigir al la vista "descargar_foto"
            
        else: #Retornar el formulario si no fue válido mostrando el error
            return render(request,"añadir_fotos/formulario.html",{
                "form":form
            })
        
    
    return render(request,"añadir_fotos/formulario.html",{
        "evento":evento,
        "form":FotografiaForm()
    })

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
    session = PhotoboothSession.objects.create(
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
        'return_url': request.META.get('HTTP_REFERER', f'/eventos/{evento_id}/')
    })

@csrf_exempt
def save_session_photo(request):
    """Guarda una foto tomada durante la sesión"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'})
    
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        frame_index = data.get('frame_index')
        image_data = data.get('image_data')
        
        if not session_id or frame_index is None or not image_data:
            return JsonResponse({'success': False, 'error': 'Datos incompletos'})
        
        # Obtener la sesión
        session = get_object_or_404(PhotoboothSession, session_id=session_id)
        
        # Procesar la imagen desde el data URL
        format, imgstr = image_data.split(';base64,')
        ext = format.split('/')[-1]
        
        # Crear un nombre de archivo único
        filename = f"session_{session_id}_frame_{frame_index}.{ext}"
        filepath = os.path.join(settings.MEDIA_ROOT, 'session_photos', filename)
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Guardar la imagen
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(imgstr))
        
        # Crear o actualizar el registro en la base de datos
        photo, created = SessionPhoto.objects.update_or_create(
            session=session,
            frame_index=frame_index,
            defaults={
                'image': f'session_photos/{filename}'
            }
        )
        
        return JsonResponse({'success': True, 'photo_id': photo.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def session_result(request, session_id):
    """Muestra el resultado de una sesión de photobooth"""
    session = get_object_or_404(PhotoboothSession, session_id=session_id)
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
        form = FotografiaForm(request.POST, request.FILES)
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
        form = FotografiaForm()

    return render(request, "fotografias/subir_foto.html", {"form": form})

#Envío de las fotos a facebook
def publicar_foto_facebook(request, foto_id):
    foto = get_object_or_404(Fotografia, id=foto_id)
    page_id = settings.FACEBOOK_PAGE_ID  # 📌 Obtiene el Page ID desde settings.py
    access_token = settings.FACEBOOK_ACCESS_TOKEN  # 📌 Obtiene el Token de Página

    # Reemplazar la URL local con la de ngrok
    imagen_url = request.build_absolute_uri(foto.img.url).replace(
        "http://127.0.0.1:8000", "hhttps://22b3-179-15-25-167.ngrok-free.app "
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
class EventoListView(ListView):
    model = Evento
    context_object_name = 'eventos'
    paginate_by = 10
    template_name = 'eventos/evento_list.html'
    
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

def añadir_foto(request, evento_id): #Función que retorna el formulario para añadir una foto a un evento
    if not request.user.is_authenticated: #Si el usuario no está autenticado...
        return redirect("login") #Redirigir al login
    
    if  not request.user.is_superuser:  #Si no es un superusuario...
     return HttpResponse("No estás autorizado para acceder a esta página") #Retornar mensaje de error
    evento=Evento.objects.get(id=evento_id) #Obtener un evento en específico
    
    if request.method=="POST": #Si la petición es POST
        form=AñadirFotoForm(request.POST, request.FILES) #Llamar al formulario
        if form.is_valid(): #Si el formulario es válido obtener los datos
            descripcion=form.cleaned_data["descripcion"]
            img=form.cleaned_data["img"]
            fotografia=Fotografia.objects.create(descripcion=descripcion, img=img, evento=evento)#Crear un objeto de Fotografia
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
'''def get_available_printers():
    printers = [printer[2] for printer in win32print.EnumPrinters(2)]
    return printers

def list_printers(request):
    printers = get_available_printers()
    return JsonResponse({'printers': printers})'''

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

@csrf_exempt
def print_document(request):
    print("solicitud de impresión recibida")
    if request.method != 'POST':
        return HttpResponseBadRequest("Método no permitido.")

    # Leer datos JSON del body
    try:
        data = json.loads(request.body)
        printer_name = data.get('printer_name')
        document_content = data.get('document_content')
        paper_size = data.get('paper_size', 'A4')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Error al leer los datos JSON.'}, status=400)

    # Verificar que los datos esenciales estén presentes
    if not printer_name or not document_content:
        return JsonResponse({'error': 'Nombre de impresora y contenido del documento son obligatorios.'}, status=400)

    try:
        # Abrir la impresora seleccionada
        printer_handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(printer_handle, 2)

        # Crear el contexto de impresión
        hprinter = win32ui.CreateDC()
        hprinter.CreatePrinterDC(printer_name)
        hprinter.StartDoc('Documento Django')
        hprinter.StartPage()

        # Ajustar fuente y formato para imprimir
        hprinter.TextOut(100, 100, document_content)  # Ajusta las coordenadas y el contenido del texto
        hprinter.EndPage()
        hprinter.EndDoc()

        hprinter.DeleteDC()
        win32print.ClosePrinter(printer_handle)

        return JsonResponse({'message': 'Documento enviado a impresión correctamente.'})

    except win32print.error as e:
        return JsonResponse({'error': f'Error de impresión: {str(e)}'}, status=500)

    except Exception as e:
        return JsonResponse({'error': f'Error inesperado: {str(e)}'}, status=500)

@csrf_exempt
def list_printers(request):
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return JsonResponse({'printers': printers})
    except Exception as e:
        return JsonResponse({'error': f'Error al obtener las impresoras: {str(e)}'}, status=500)






