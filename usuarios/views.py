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

import requests


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