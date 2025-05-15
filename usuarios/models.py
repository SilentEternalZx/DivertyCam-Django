import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from multiselectfield import MultiSelectField


# Modelo de Usuario personalizado
class User(AbstractUser):
   pass


#Modelo de invitado
class Invitado(models.Model):
    nombre=models.CharField(max_length=20)
    telefono=models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return f'{self.nombre} {self.telefono}'
    
#Modelo de cliente
class Cliente(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre"),
        help_text=_("Nombre del cliente")
    )
    
    usuario=models.ForeignKey(User,related_name="cliente" , on_delete=models.CASCADE, null=True)
    
    apellido = models.CharField(
        max_length=100,
        verbose_name=_("Apellido"),
        help_text=_("Apellido del cliente")
    )
    
    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Cédula"),
        help_text=_("Número de cédula o documento de identidad"),
        db_index=True
    )
    
    fechaNacimiento = models.DateField(
        verbose_name=_("Fecha de Nacimiento"),
        help_text=_("Fecha de nacimiento del cliente")
    )
    
    direccion = models.CharField(
        max_length=255,
        verbose_name=_("Dirección"),
        help_text=_("Dirección completa del cliente")
    )
    
    correo = models.EmailField(
        unique=True,
        verbose_name=_("Correo Electrónico"),
        help_text=_("Correo electrónico del cliente"),
        db_index=True
    )
    
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos.")
    )
    
    telefono = models.CharField(
        validators=[telefono_regex],
        max_length=17,
        verbose_name=_("Teléfono"),
        help_text=_("Número de teléfono del cliente")
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Creación")
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de Actualización")
    )
    activo = models.BooleanField(default=True)  # Nuevo campo para indicar si está activo
    
    # Campo para búsquedas full-text en PostgreSQL
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['correo']),
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.cedula}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # El vector de búsqueda se actualizará en el signal post_save

@receiver(post_save, sender=Cliente)
def update_search_vector(sender, instance, **kwargs):
    Cliente.objects.filter(pk=instance.pk).update(search_vector=
        SearchVector('nombre', weight='A') +
        SearchVector('apellido', weight='A') +
        SearchVector('cedula', weight='B') +
        SearchVector('correo', weight='B') +
        SearchVector('direccion', weight='C')
    )


class CategoriaEvento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    album_facebook_id = models.CharField(max_length=50, null=True, blank=True)  # ID del álbum en Facebook

    def __str__(self):
        return self.nombre

#Modelo de eventos
class Evento(models.Model):
    SERVICIOS_CHOICES = [
        ('photobook', _('Photobook')),
        ('foto_tradicional', _('Foto tradicional')),
        ('video', _('Video')),
        ('cabina_360', _('Cabina 360')),
        ('cabina_fotos', _('Cabina fotos')),
        ('drone', _('Drone')),
        ('clip_inicio', _('Clip de inicio')),
    ]
    
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre del evento"))
    fecha_hora = models.DateTimeField(verbose_name=_("Fecha y hora del evento"))
    servicios = MultiSelectField(choices=SERVICIOS_CHOICES, max_length=100, verbose_name=_("Servicios"))
    direccion = models.CharField(max_length=255, verbose_name=_("Dirección del evento"))
    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name=_("Cliente")
    )
    categoria = models.ForeignKey(
        CategoriaEvento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Categoría"),
        help_text=_("Selecciona la categoría del evento")
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre del evento"),
        help_text=_("Nombre o título del evento")
    )
    
    fecha_hora = models.DateTimeField(
        verbose_name=_("Fecha y hora del evento"),
        help_text=_("Fecha y hora programada para el evento")
    )
    
    servicios = MultiSelectField(
        choices=SERVICIOS_CHOICES,
        max_choices=7,
        max_length=100,
        verbose_name=_("Servicios"),
        help_text=_("Servicios contratados para el evento")
    )
    
    direccion = models.CharField(
        max_length=255,
        verbose_name=_("Dirección del evento"),
        help_text=_("Dirección completa donde se realizará el evento")
    )
    
    # Usamos el string completo para el modelo Cliente en lugar de solo 'Cliente'
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name=_("Cliente"),
        help_text=_("Cliente asociado al evento")
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Fecha de Creación")
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Fecha de Actualización")
    )
    
    # Campo para búsquedas full-text en PostgreSQL
    search_vector = SearchVectorField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Evento")
        verbose_name_plural = _("Eventos")
        ordering = ["-fecha_hora"]
        indexes = [
            models.Index(fields=["fecha_hora"]),
            models.Index(fields=["cliente"]),
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')} - {self.cliente}"
    
class Configurar_Photobooth(models.Model):
    evento = models.OneToOneField(Evento, on_delete=models.CASCADE, related_name='config_photobooth')
    mensaje_bienvenida = models.CharField(max_length=255, default='¡Bienvenidos a nuestro photobooth!')
    imagen_fondo = models.ImageField(upload_to='photobooth/fondos/', null=True, blank=True)
    color_texto = models.CharField(max_length=7, default='#000000')
    tamano_texto = models.IntegerField(default=24)
    tipo_letra = models.CharField(max_length=50, default='Arial')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Configuración de cámara
    camera_id = models.CharField(max_length=255, blank=True, null=True, verbose_name="ID de cámara seleccionada")
    
    # Nueva configuración para resolución y balance de blancos
    RESOLUCION_CHOICES = [
        ('640x480', '640x480 (VGA)'),
        ('1280x720', '1280x720 (HD)'),
        ('1920x1080', '1920x1080 (Full HD)'),
        ('3840x2160', '3840x2160 (4K)'),
    ]
    
    resolucion_camara = models.CharField(
        max_length=20, 
        choices=RESOLUCION_CHOICES, 
        default='1280x720',
        verbose_name="Resolución de cámara"
    )
    
    BALANCE_BLANCOS_CHOICES = [
        ('auto', 'Automático'),
        ('cloudy', 'Nublado'),
        ('sunny', 'Soleado'),
        ('fluorescent', 'Fluorescente'),
        ('incandescent', 'Incandescente'),
    ]
    
    balance_blancos = models.CharField(
        max_length=20, 
        choices=BALANCE_BLANCOS_CHOICES, 
        default='auto',
        verbose_name="Balance de blancos"
    )
    
    # Opciones para el collage de fotos
    max_fotos = models.IntegerField(default=4, choices=[(1, '1 foto'), (2, '2 fotos'), (4, '4 fotos'), (5, '5 fotos')])
    permitir_personalizar = models.BooleanField(default=True, help_text="Permitir a los usuarios mover y redimensionar fotos")
    
    def __str__(self):
        return f"Photobooth para {self.evento.nombre}"


@receiver(post_save, sender=Evento)
def update_search_vector(sender, instance, **kwargs):
    # Obtener los datos del cliente relacionado
    cliente = instance.cliente
    nombre_cliente = cliente.nombre if cliente else ""
    apellido_cliente = cliente.apellido if cliente else ""
    
    # Crear el vector de búsqueda utilizando una expresión SQL directa
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE usuarios_evento 
            SET search_vector = to_tsvector('spanish', %s) || 
                                to_tsvector('spanish', %s) ||
                                to_tsvector('spanish', %s) ||
                                to_tsvector('spanish', %s)
            WHERE id = %s
            """,
            [
                instance.nombre or "",                  # Peso A
                nombre_cliente or "",                   # Peso B
                apellido_cliente or "",                 # Peso B 
                instance.direccion or "",               # Peso C
                instance.pk
            ]
        )

class PhotoboothConfig(models.Model):
    """Modelo para almacenar la configuración del photobooth"""
    evento = models.OneToOneField(Evento, on_delete=models.CASCADE, related_name='photobooth_config')
    mensaje_bienvenida = models.CharField(max_length=200, default='¡Bienvenidos al photobooth!')
    imagen_fondo = models.ImageField(upload_to='photobooth/fondos/', blank=True, null=True)
    color_texto = models.CharField(max_length=20, default='#000000')
    tamano_texto = models.IntegerField(default=24)
    tipo_letra = models.CharField(max_length=50, default='Arial')
    
    permitir_personalizar = models.BooleanField(default=False)
    
    # Nuevo campo para integración de collages personalizables
    plantilla_collage = models.ForeignKey(
        'CollageTemplate', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='photobooth_configs'
    )
    
    # NUEVOS CAMPOS para configuración avanzada
    
    # Configuración de tiempo entre fotos
    tiempo_entre_fotos = models.IntegerField(
        default=3,
        validators=[
            MinValueValidator(1, message="El tiempo mínimo entre fotos es 1 segundo"),
            MaxValueValidator(20, message="El tiempo máximo entre fotos es 20 segundos")
        ],
        verbose_name="Tiempo entre fotos (segundos)",
        help_text="Intervalo de tiempo entre cada foto durante la sesión"
    )
    
    # Configuración de cuenta regresiva antes de la foto
    tiempo_cuenta_regresiva = models.IntegerField(
        default=3,
        validators=[
            MinValueValidator(1, message="La cuenta regresiva mínima es 1 segundo"),
            MaxValueValidator(10, message="La cuenta regresiva máxima es 10 segundos")
        ],
        verbose_name="Tiempo de cuenta regresiva",
        help_text="Cuenta regresiva antes de tomar cada foto"
    )
    
    # Configuración de cámara (ya existe pero vamos a hacerlo más completo)
    camera_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="ID de cámara seleccionada",
        help_text="Identificador de la cámara web a utilizar"
    )
    
    # Configuración de resolución
    RESOLUCION_CHOICES = [
        ('640x480', '640x480 (VGA)'),
        ('1280x720', '1280x720 (HD)'),
        ('1920x1080', '1920x1080 (Full HD)'),
        ('3840x2160', '3840x2160 (4K)'),
    ]
    
    resolucion_camara = models.CharField(
        max_length=20, 
        choices=RESOLUCION_CHOICES, 
        default='1280x720',
        verbose_name="Resolución de cámara",
        help_text="Resolución para capturar las fotos"
    )
    
    # Configuración de balance de blancos
    BALANCE_BLANCOS_CHOICES = [
        ('auto', 'Automático'),
        ('cloudy', 'Nublado'),
        ('sunny', 'Soleado'),
        ('fluorescent', 'Fluorescente'),
        ('incandescent', 'Incandescente'),
    ]
    
    balance_blancos = models.CharField(
        max_length=20, 
        choices=BALANCE_BLANCOS_CHOICES, 
        default='auto',
        verbose_name="Balance de blancos",
        help_text="Ajuste del balance de blancos de la cámara"
    )
    
    # Configuración de ISO
    iso_valor = models.IntegerField(
        default=100,
        validators=[
            MinValueValidator(100, message="El ISO mínimo es 100"),
            MaxValueValidator(3200, message="El ISO máximo es 3200")
        ],
        verbose_name="Valor ISO",
        help_text="Sensibilidad ISO de la cámara"
    )
    
    # CONFIGURACIÓN DE IMPRESORA
    printer_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Impresora seleccionada",
        help_text="Nombre de la impresora a utilizar para imprimir los collages"
    )
    
    # Tamaño de papel para impresión
    PAPER_SIZE_CHOICES = [
        ('10x15', '10x15 cm (4x6 pulgadas)'),
        ('13x18', '13x18 cm (5x7 pulgadas)'),  
        ('15x20', '15x20 cm (6x8 pulgadas)'),
        ('20x25', '20x25 cm (8x10 pulgadas)'),
        ('A4', 'A4 (21x29.7 cm)'),
        ('Letter', 'Letter (8.5x11 pulgadas)')
    ]
    
    paper_size = models.CharField(
        max_length=50,
        choices=PAPER_SIZE_CHOICES,
        default='10x15',
        verbose_name="Tamaño de papel",
        help_text="Tamaño del papel para impresión de collages"
    )
    
    # Número de copias por defecto
    copias_impresion = models.IntegerField(
        default=1,
        validators=[
            MinValueValidator(1, message="Debe imprimir al menos 1 copia"),
            MaxValueValidator(10, message="Máximo 10 copias por impresión")
        ],
        verbose_name="Copias a imprimir",
        help_text="Número de copias a imprimir por defecto"
    )
    
    # Configuración de calidad de impresión
    CALIDAD_IMPRESION_CHOICES = [
        ('draft', 'Borrador'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('best', 'Máxima')
    ]
    
    calidad_impresion = models.CharField(
        max_length=20,
        choices=CALIDAD_IMPRESION_CHOICES,
        default='high',
        verbose_name="Calidad de impresión",
        help_text="Calidad de impresión para los collages"
    )
    
    # Activar/desactivar impresión automática
    imprimir_automaticamente = models.BooleanField(
        default=False,
        verbose_name="Imprimir automáticamente",
        help_text="Si está activado, imprime automáticamente al finalizar el collage"
    )
    
    # CONFIGURACIÓN DE VISUALIZACIÓN DE FOTOS
    tiempo_visualizacion_foto = models.IntegerField(
        default=2,
        validators=[
            MinValueValidator(1, message="El tiempo mínimo de visualización es 1 segundo"),
            MaxValueValidator(10, message="El tiempo máximo de visualización es 10 segundos")
        ],
        verbose_name="Tiempo de visualización de foto",
        help_text="Tiempo que se muestra cada foto antes de continuar"
    )
    
    # Estado del photobooth
    activo = models.BooleanField(
        default=True,
        verbose_name="Photobooth activo",
        help_text="Indica si el photobooth está activo para este evento"
    )
    
    # Registro de uso
    total_sesiones = models.IntegerField(
        default=0,
        verbose_name="Total de sesiones",
        help_text="Número total de sesiones completadas"
    )
    
    total_fotos = models.IntegerField(
        default=0,
        verbose_name="Total de fotos",
        help_text="Número total de fotos tomadas"
    )
    
    total_impresiones = models.IntegerField(
        default=0,
        verbose_name="Total de impresiones",
        help_text="Número total de collages impresos"
    )
    
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Configuración de Photobooth"
        verbose_name_plural = "Configuraciones de Photobooth"
    
    def __str__(self):
        return f"Configuración Photobooth - {self.evento.nombre}"
    
    def incrementar_sesiones(self):
        """Incrementa el contador de sesiones completadas"""
        self.total_sesiones += 1
        self.save()
    
    def incrementar_fotos(self, cantidad=1):
        """Incrementa el contador de fotos tomadas"""
        self.total_fotos += cantidad
        self.save()
    
    def incrementar_impresiones(self, cantidad=1):
        """Incrementa el contador de impresiones realizadas"""
        self.total_impresiones += cantidad
        self.save()

class CollageTemplate(models.Model):
    """Modelo para almacenar plantillas de collage personalizadas"""
    template_id = models.CharField(max_length=36, primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    background_color = models.CharField(max_length=20, default='#FFFFFF')
    background_image = models.ImageField(upload_to='collage/backgrounds/', null=True, blank=True)
    background_size = models.CharField(max_length=20, default='cover')
    background_position = models.CharField(max_length=20, default='center')
    background_repeat = models.CharField(max_length=20, default='no-repeat')
    template_data = models.TextField(help_text="Datos completos de la plantilla en formato JSON")
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='collage_templates')
    es_predeterminada = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.template_id})"
    
    def get_frames(self):
        """Obtiene los marcos de fotos de la plantilla"""
        try:
            data = json.loads(self.template_data)
            return data.get('frames', [])
        except:
            return []
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Plantilla de Collage"
        verbose_name_plural = "Plantillas de Collage"

class CollageSession(models.Model):
    """Modelo para almacenar sesiones de fotos basadas en plantillas"""
    STATUS_CHOICES = (
        ('active', 'Activa'),
        ('completed', 'Completada'),
        ('canceled', 'Cancelada'),
    )
    
    session_id = models.CharField(max_length=36, primary_key=True)
    template = models.ForeignKey(CollageTemplate, on_delete=models.CASCADE, related_name='sessions')
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='collage_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Sesión {self.session_id} - {self.evento.nombre}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Sesión de Collage"
        verbose_name_plural = "Sesiones de Collage"


# class PhotoboothSession(models.Model):
#     """Modelo para representar una sesión de photobooth"""
#     evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='photobooth_sessions')
#     template = models.ForeignKey(CollageTemplate, on_delete=models.SET_NULL, null=True, blank=True)
#     session_id = models.CharField(max_length=50, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"Sesión {self.session_id} - {self.evento.nombre}"

class SessionPhoto(models.Model):
    """Modelo para almacenar fotos tomadas durante una sesión"""
    session = models.ForeignKey(CollageSession, on_delete=models.CASCADE, related_name='photos')
    frame_index = models.IntegerField(help_text="Índice del marco en la plantilla")
    image = models.ImageField(upload_to='collage/session_photos/')
    taken_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Foto {self.frame_index} de sesión {self.session.session_id}"
    
    class Meta:
        ordering = ['session', 'frame_index']
        verbose_name = "Foto de Sesión"
        verbose_name_plural = "Fotos de Sesión"
        unique_together = ('session', 'frame_index')  # Una foto por marco en cada sesión

class CollageResult(models.Model):
    """Modelo para almacenar los collages finales generados"""
    collage_id = models.CharField(max_length=36, primary_key=True)
    session = models.OneToOneField(CollageSession, on_delete=models.CASCADE, related_name='result')
    image = models.ImageField(upload_to='collage/results/')
    created_at = models.DateTimeField(auto_now_add=True)
    print_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Collage {self.collage_id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Resultado de Collage"
        verbose_name_plural = "Resultados de Collage"
#Modelo de fotografia
class Fotografia(models.Model):
    
    img=models.ImageField(null=True,blank=True, upload_to="imagenes/")
    descripcion=models.TextField()
    invitado=models.ForeignKey(Invitado, related_name="fotografias", on_delete=models.CASCADE, null=True)
    evento=models.ForeignKey(Evento, related_name="fotografias", on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.descripcion} {self.invitado}'
