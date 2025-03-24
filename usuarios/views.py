from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.core.files.base import ContentFile
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
from .forms import ClienteForm, CollageTemplateForm, EventoForm, PhotoboothConfigForm
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from .models import Evento, Configurar_Photobooth, CollageTemplate
from .forms import Configurar_PhotoboothForm
import json
import uuid
import base64
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import logging

logger = logging.getLogger(__name__)


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
    """Vista para configurar el photobooth de un evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    config, created = PhotoboothConfig.objects.get_or_create(evento=evento)
    
    template_id = request.GET.get('template')
    
    if request.method == 'POST':
        form = PhotoboothConfigForm(
            request.POST, 
            request.FILES, 
            instance=config, 
            evento=evento
        )
        if form.is_valid():
            config = form.save(commit=False)
            config.evento = evento
            config.save()
            messages.success(request, "Configuración guardada correctamente")
            return redirect('configurar_photobooth', evento_id=evento.id)
    else:
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
    
    context = {
        'evento': evento,
        'form': form,
        'config': config,
        'selected_template': selected_template,
        'frames': frames
    }
    
    return render(request, 'photobooth/configurar_photobooth.html', context)

def preview_photobooth(request, evento_id):
    """Vista para mostrar la vista previa del photobooth"""
    evento = get_object_or_404(Evento, id=evento_id)
    config = PhotoboothConfig.objects.filter(evento=evento).first()
    
    context = {
        'evento': evento,
        'config': config
    }
    
    return render(request, 'photobooth/preview_photobooth.html', context)

def template_list(request, evento_id):
    """Vista para listar las plantillas de collage disponibles para un evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    templates = CollageTemplate.objects.filter(evento=evento)
    
    context = {
        'evento': evento,
        'templates': templates
    }
    
    return render(request, 'collage/template_list.html', context)

def template_editor(request, evento_id, template_id=None):
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
    """Iniciar una sesión de fotos con una plantilla específica"""
    evento = get_object_or_404(Evento, id=evento_id)
    template = get_object_or_404(CollageTemplate, template_id=template_id, evento=evento)
    
    # Crear una nueva sesión
    session = CollageSession.objects.create(
        session_id=str(uuid.uuid4()),
        template=template,
        evento=evento,
        status='active'
    )
    
    # Convertir datos de la plantilla para el frontend
    template_data = json.loads(template.template_data)
    template_json = json.dumps(template_data)
    
    context = {
        'evento': evento,
        'template': template,
        'template_json': template_json,
        'session_id': session.session_id
    }
    
    return render(request, 'collage/collage_session.html', context)

@csrf_exempt
@require_POST
def save_session_photo(request):
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
