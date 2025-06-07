import json
from time import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from multiselectfield import MultiSelectField
from django.forms.widgets import ClearableFileInput
from django.core.validators import MinLengthValidator
# Modelo de Usuario personalizado
class User(AbstractUser):
   pass


class CustomGroup(Group):
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
        max_length=50, 
        verbose_name=_("Nombre"),
        validators=[MinLengthValidator(3, 'El nombre debe ser de al menos 3 caracteres')]
        
    )
    
    
    usuario=models.ForeignKey(User,related_name="cliente" , on_delete=models.CASCADE, null=True)
    
    apellido = models.CharField(
        
        max_length=50,
        verbose_name=_("Apellido"),
         validators=[MinLengthValidator(3, 'El apellido debe ser de al menos 3 caracteres')]
       
     
    )
    

    
    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Cédula"),
        validators=[MinLengthValidator(5, 'La cédula debe tener al menos 5 dígitos.')],
       
        db_index=True
    )
    
    fechaNacimiento = models.DateField(
        verbose_name=_("Fecha de Nacimiento"),
        
    )
    
    direccion = models.CharField(
        max_length=50,
        verbose_name=_("Dirección"),
        validators=[MinLengthValidator(5, 'La dirección debe tener al menos 5 caracteres.')],
      
    )
    
 
    
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos.")
    )
    
    telefono = models.CharField(
        validators=[telefono_regex],
        max_length=17,
        verbose_name=_("Teléfono"),
        
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
        SearchVector('direccion', weight='C')
    )


class CategoriaEvento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    album_facebook_id = models.CharField(max_length=50, null=False, blank=False)  # ID del álbum en Facebook

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
    
    nombre = models.CharField(max_length=100, verbose_name=_("Nombre del evento"),
    validators=[MinLengthValidator(7, 'El nombre del evento debe tener al menos 7 caracteres')]),
    fecha_hora = models.DateTimeField(verbose_name=_("Fecha y hora del evento"))
    servicios = MultiSelectField(choices=SERVICIOS_CHOICES, verbose_name=_("Servicios"),
                                validators= [MinLengthValidator(1, 'El evento debe contener al menos 1 servicio')])
    
    direccion = models.CharField(max_length=50, verbose_name=_("Dirección del evento"),
                                 validators=[MinLengthValidator(7, 'La dirección debe tener al menos 7 caracteres.')])
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
        
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    search_vector = SearchVectorField(null=True, blank=True)

    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre del evento"),
        
    )
    
    fecha_hora = models.DateTimeField(
        verbose_name=_("Fecha y hora del evento"),
      
    )
    
    servicios = MultiSelectField(
        choices=SERVICIOS_CHOICES,
        max_choices=7,
        max_length=100,
        verbose_name=_("Servicios"),
        
    )
    
    direccion = models.CharField(
        max_length=255,
        verbose_name=_("Dirección del evento"),
        
    )
    
    # Usamos el string completo para el modelo Cliente en lugar de solo 'Cliente'
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name=_("Cliente"),
        
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
    
   

        # NUEVOS CAMPOS para control de iluminación y cámara
    nivel_iluminacion = models.IntegerField(
        default=50,
        validators=[
            MinValueValidator(0, message="El nivel mínimo de iluminación es 0"),
            MaxValueValidator(100, message="El nivel máximo de iluminación es 100")
        ],
        verbose_name="Nivel de iluminación (%)",
        help_text="Ajuste de brillo/iluminación de 0 a 100"
    )
    
    # Tipo de cámara
    CAMERA_TYPE_CHOICES = [
    ('webcam', 'Cámara Web'),
    ('nikon_dslr', 'Nikon DSLR/Mirrorless'),
    ('usb_ptp', 'Cámara USB (PTP)'),  # NUEVA OPCIÓN
    ('canon_dslr', 'Canon DSLR'),      # NUEVA OPCIÓN
    ('sony_camera', 'Sony Camera'),     # NUEVA OPCIÓN
    ('windows_camera', 'Cámara Windows (WIA/PTP)'),
]
        # Información de conexión USB
    usb_vendor_id = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="USB Vendor ID",
        help_text="ID del fabricante USB (ej: 04b0 para Nikon)"
    )
    
    usb_product_id = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name="USB Product ID", 
        help_text="ID del producto USB específico"
    )
    
    usb_serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Número de serie USB",
        help_text="Número de serie de la cámara USB conectada"
    )
    
    # Estado de conexión USB
    usb_session_id = models.CharField(
        max_length=36,
        blank=True,
        null=True,
        verbose_name="ID de sesión USB",
        help_text="Identificador único de la sesión USB activa"
    )
    
    usb_connection_status = models.CharField(
        max_length=20,
        choices=[
            ('disconnected', 'Desconectada'),
            ('connecting', 'Conectando'),
            ('connected', 'Conectada'),
            ('error', 'Error'),
        ],
        default='disconnected',
        verbose_name="Estado de conexión USB"
    )
    
    # Configuraciones avanzadas USB
    usb_use_raw_mode = models.BooleanField(
        default=False,
        verbose_name="Usar modo RAW",
        help_text="Capturar en formato RAW si está disponible"
    )
    
    usb_auto_download = models.BooleanField(
        default=True,
        verbose_name="Descarga automática",
        help_text="Descargar automáticamente las fotos después de capturar"
    )
    
    usb_delete_after_download = models.BooleanField(
        default=False,
        verbose_name="Eliminar después de descargar",
        help_text="Eliminar fotos de la cámara después de descargarlas"
    )
    
    # Timeouts y configuraciones de conexión
    usb_connection_timeout = models.IntegerField(
        default=10,
        verbose_name="Timeout de conexión (segundos)",
        help_text="Tiempo máximo para establecer conexión USB"
    )
    
    usb_capture_timeout = models.IntegerField(
        default=30,
        verbose_name="Timeout de captura (segundos)",
        help_text="Tiempo máximo para completar una captura"
    )
    
    # Log de actividad USB
    usb_last_connected = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Última conexión USB"
    )
    
    usb_last_error = models.TextField(
        blank=True,
        null=True,
        verbose_name="Último error USB"
    )
    
    usb_total_captures = models.IntegerField(
        default=0,
        verbose_name="Total capturas USB",
        help_text="Contador de fotos capturadas vía USB"
    )
    
    def update_usb_connection_status(self, status, error_message=None):
        """Actualiza el estado de conexión USB"""
        self.usb_connection_status = status
        if error_message:
            self.usb_last_error = error_message
        if status == 'connected':
            self.usb_last_connected = timezone.now()
        self.save()
    
    def increment_usb_captures(self):
        """Incrementa el contador de capturas USB"""
        self.usb_total_captures += 1
        self.save()
    
    def get_usb_camera_info(self):
        """Retorna información de la cámara USB conectada"""
        if self.usb_vendor_id and self.usb_product_id:
            return {
                'vendor_id': self.usb_vendor_id,
                'product_id': self.usb_product_id,
                'serial_number': self.usb_serial_number,
                'session_id': self.usb_session_id,
                'status': self.usb_connection_status,
                'last_connected': self.usb_last_connected,
                'total_captures': self.usb_total_captures
            }
        return None

    tipo_camara = models.CharField(
        max_length=20,
        choices=CAMERA_TYPE_CHOICES,
        default='webcam',
        verbose_name="Tipo de cámara",
        help_text="Tipo de cámara a utilizar"
    )
    
    # Información de la cámara Nikon conectada
    nikon_camera_model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modelo de cámara Nikon",
        help_text="Modelo detectado automáticamente"
    )
    
    # Configuraciones DSLR
    velocidad_obturacion = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default='1/125',
        verbose_name="Velocidad de obturación",
        help_text="Ej: 1/125, 1/60, 1/30"
    )
    
    apertura = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        default='f/5.6',
        verbose_name="Apertura (f-stop)",
        help_text="Ej: f/2.8, f/4, f/5.6"
    )
    
    modo_disparo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        default='M',
        verbose_name="Modo de disparo",
        choices=[
            ('M', 'Manual'),
            ('A', 'Prioridad de Apertura'),
            ('S', 'Prioridad de Obturación'),
            ('P', 'Programa'),
        ]
    )
    
    # Calidad de imagen
    calidad_imagen = models.CharField(
        max_length=20,
        default='JPEG_FINE',
        choices=[
            ('RAW', 'RAW (NEF)'),
            ('JPEG_FINE', 'JPEG Fine'),
            ('JPEG_NORMAL', 'JPEG Normal'),
            ('RAW_JPEG', 'RAW + JPEG'),
        ],
        verbose_name="Calidad de imagen"
    )
    
    # Control de enfoque
    modo_enfoque = models.CharField(
        max_length=20,
        default='AF-S',
        choices=[
            ('AF-S', 'AF Simple (AF-S)'),
            ('AF-C', 'AF Continuo (AF-C)'),
            ('MF', 'Manual (MF)'),
        ],
        verbose_name="Modo de enfoque"
    )
    
    # Puerto del servidor qDslrDashboard
    qdslr_server_port = models.IntegerField(
        default=4757,
        verbose_name="Puerto del servidor qDslrDashboard",
        help_text="Puerto donde corre el servidor (default: 4757)"
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

# Nuevo modelo para almacenar información detallada de cámaras USB
class USBCameraInfo(models.Model):
    """Modelo para almacenar información detallada de cámaras USB detectadas"""
    
    vendor_id = models.CharField(max_length=10, verbose_name="Vendor ID")
    product_id = models.CharField(max_length=10, verbose_name="Product ID")
    vendor_name = models.CharField(max_length=100, verbose_name="Fabricante")
    product_name = models.CharField(max_length=100, verbose_name="Modelo")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Número de serie")
    
    # Capacidades detectadas
    supports_ptp = models.BooleanField(default=False, verbose_name="Soporta PTP")
    supports_liveview = models.BooleanField(default=False, verbose_name="Soporta LiveView")
    supports_remote_capture = models.BooleanField(default=False, verbose_name="Soporta captura remota")
    
    # Configuraciones soportadas
    supported_iso_values = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Valores ISO soportados"
    )
    supported_apertures = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Aperturas soportadas"
    )
    supported_shutter_speeds = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Velocidades de obturación soportadas"
    )
    
    # Metadatos
    first_detected = models.DateTimeField(auto_now_add=True, verbose_name="Primera detección")
    last_seen = models.DateTimeField(auto_now=True, verbose_name="Última vez vista")
    times_connected = models.IntegerField(default=0, verbose_name="Veces conectada")
    
    class Meta:
        verbose_name = "Información de Cámara USB"
        verbose_name_plural = "Información de Cámaras USB"
        unique_together = ('vendor_id', 'product_id', 'serial_number')
    
    def __str__(self):
        return f"{self.vendor_name} {self.product_name} ({self.vendor_id}:{self.product_id})"
    
    def increment_connection_count(self):
        """Incrementa el contador de conexiones"""
        self.times_connected += 1
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
    
    img=models.ImageField(null=False, blank=False, upload_to="imagenes/")
    descripcion=models.TextField(max_length=34,   
                                 validators=[MinLengthValidator(5, 'La descripción debe tener al menos 5 caracteres.')],)
    invitados=models.ManyToManyField('Invitado', related_name="fotografias", null=True)
    evento=models.ForeignKey(Evento, related_name="fotografias", on_delete=models.CASCADE)
    
    def __str__(self):
        invitados_str = ", ".join([str(inv) for inv in self.invitados.all()])
        return f'{self.descripcion} | Invitados: {invitados_str}'





    
# Agregar este modelo a tu models.py existente

class WhatsAppTransfer(models.Model):
    """Modelo para registrar transferencias de collages por WhatsApp"""
    
    STATUS_CHOICES = [
        ('sent_to_device', 'Enviado al dispositivo'),
        ('data_collected', 'Datos recopilados'),
        ('whatsapp_sent', 'Enviado por WhatsApp'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.AutoField(primary_key=True)
    session = models.ForeignKey(
        CollageSession, 
        on_delete=models.CASCADE, 
        related_name='whatsapp_transfers'
    )
    collage_result = models.ForeignKey(
        CollageResult, 
        on_delete=models.CASCADE, 
        related_name='whatsapp_transfers',
        null=True,
        blank=True
    )
    
    # Datos del usuario recopilados
    phone_number = models.CharField(
        max_length=20, 
        verbose_name="Número de teléfono",
        help_text="Número de WhatsApp del usuario"
    )
    user_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Nombre del usuario"
    )
    user_email = models.EmailField(
        blank=True, 
        null=True,
        verbose_name="Email del usuario"
    )
    
    # Estado y metadatos de la transferencia
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='sent_to_device',
        verbose_name="Estado de la transferencia"
    )
    
    transfer_timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Momento de la transferencia"
    )
    
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Completado en"
    )
    
    # Metadatos adicionales
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadatos adicionales",
        help_text="Información adicional sobre la transferencia"
    )
    
    # Información del dispositivo usado
    device_model = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Modelo del dispositivo"
    )
    
    device_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="ID del dispositivo"
    )
    
    # Mensaje personalizado enviado
    custom_message = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Mensaje personalizado",
        help_text="Mensaje personalizado enviado con el collage"
    )
    
    # Errores y logs
    error_message = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Mensaje de error"
    )
    
    retry_count = models.IntegerField(
        default=0,
        verbose_name="Intentos de reenvío"
    )
    
    class Meta:
        verbose_name = "Transferencia de WhatsApp"
        verbose_name_plural = "Transferencias de WhatsApp"
        ordering = ['-transfer_timestamp']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['transfer_timestamp']),
            models.Index(fields=['session']),
        ]
    
    def __str__(self):
        return f"WhatsApp Transfer {self.id} - {self.session.session_id} - {self.status}"
    
    @property
    def is_completed(self):
        """Indica si la transferencia se completó exitosamente"""
        return self.status in ['whatsapp_sent', 'completed']
    
    @property
    def duration(self):
        """Calcula la duración de la transferencia"""
        if self.completed_at and self.transfer_timestamp:
            return self.completed_at - self.transfer_timestamp
        return None
    
    def mark_as_completed(self, custom_message=None):
        """Marca la transferencia como completada"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if custom_message:
            self.custom_message = custom_message
        self.save()
    
    def mark_as_failed(self, error_message):
        """Marca la transferencia como fallida"""
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()
    
    def get_summary(self):
        """Retorna un resumen de la transferencia"""
        return {
            'id': self.id,
            'session_id': self.session.session_id,
            'evento': self.session.evento.nombre,
            'phone_number': self.phone_number,
            'user_name': self.user_name,
            'status': self.get_status_display(),
            'transfer_timestamp': self.transfer_timestamp.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration': str(self.duration) if self.duration else None,
            'is_completed': self.is_completed,
        }