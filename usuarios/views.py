from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .models import*
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cliente
from .forms import ClienteForm, FotografiaForm, RegistroForm, EventoForm,AñadirFotoForm
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.contrib.messages.views import SuccessMessageMixin
from django.http import StreamingHttpResponse
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json
import cv2
import os
import time
import datetime
import win32print
import win32ui
import requests
import uuid


def index(request):  #Función  para retornar vista principal
    return render(request, "index/index.html")


def vista_login(request): #Función para iniciar sesión
    mensaje = ""  # Mensaje de error si las credenciales fallan
    if request.method == "POST":  #Si la petición es un POST, capturar los datos
        nombre_usuario = request.POST.get("nombre_usuario")
        contraseña = request.POST.get("contraseña")
        usuario = authenticate(request, username=nombre_usuario, password=contraseña)


        if usuario is not None:  #Si el usuario existe
            login(request, usuario) #Logearse
            return redirect("index")  # Redirige a la página principal tras iniciar sesión
        else:  #De lo contrario mostrar mensaje de error
            mensaje = "Usuario o contraseña inválidos"

    return render(request, "login/login.html", {
        "mensaje": mensaje
        })

# Cerrar sesión
@login_required
def vista_logout(request): #Función para cerrar sesión
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

def impresoras(request):
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return render(request, 'impresoras/impresoras.html', {'printers': printers})
    except Exception as e:
        return render(request, 'impresoras/impresoras.html', {'error': str(e)})

@csrf_exempt
def print_document(request):
    print("solicitud de impresión recivida")
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






