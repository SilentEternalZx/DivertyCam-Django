import json
from django import forms
import json
from .models import *

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
import re
from django.utils import timezone
from django.db.models import Q



User = get_user_model()

class CustomPasswordResetForm(PasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Este correo no está registrado.")
        return email
    
class ClienteForm(forms.ModelForm):

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'cedula', 'fechaNacimiento',
                  'direccion', 'telefono', 'usuario']
        widgets = {
            'fechaNacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'fechaNacimiento'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clientes = Cliente.objects.values_list('usuario_id', flat=True)

        if self.instance.pk and self.instance.usuario:
            self.fields['usuario'].queryset = User.objects.filter(
                is_superuser=False
            ).filter(
                Q(~Q(id__in=clientes)) | Q(id=self.instance.usuario.pk)
            )
        else:
            self.fields['usuario'].queryset = User.objects.filter(
                is_superuser=False
            ).exclude(id__in=clientes)
            
              # Forzar formato YYYY-MM-DD para el campo fechaNacimiento
        if self.instance and self.instance.pk and self.instance.fechaNacimiento:
         self.initial['fechaNacimiento'] = self.instance.fechaNacimiento.strftime('%Y-%m-%d')

    def clean_fechaNacimiento(self):
        fechaNacimiento = self.cleaned_data.get('fechaNacimiento')
        if fechaNacimiento:
            import datetime
            hoy = datetime.date.today()
            edad = hoy.year - fechaNacimiento.year - (
                (hoy.month, hoy.day) < (fechaNacimiento.month, fechaNacimiento.day)
            )
            if edad < 18:
                raise forms.ValidationError("El cliente debe ser mayor de edad (18 años o más).")
        return fechaNacimiento

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not cedula.isdigit():
            raise forms.ValidationError("La cédula debe contener solo números.")
        if not (6 <= len(cedula) <= 10):
            raise forms.ValidationError("La cédula debe tener entre 6 y 10 dígitos.")
        return cedula
      


class RegistroForm(UserCreationForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=20,
        help_text="La contraseña debe tener entre 8 y 20 caracteres.",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=20,
        help_text="Ingresa la misma contraseña para confirmar.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_username(self):
        username = self.cleaned_data.get('username', '')

        # Longitud
        if not (6 <= len(username) <= 30):
            raise forms.ValidationError("El nombre de usuario debe tener entre 6 y 30 caracteres.")

        # Alfanumérico y espacios
        if not re.match(r'^[\w\s]+$', username):
            raise forms.ValidationError("El nombre de usuario solo puede contener letras, números y espacios.")

        # No vacío (por claridad, aunque la longitud ya lo cubre)
        if not username.strip():
            raise forms.ValidationError("El nombre de usuario no puede estar vacío.")

        return username
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')

        # Longitud
        if not (8 <= len(password) <= 15):
            raise forms.ValidationError("La contraseña debe tener entre 8 y 15 caracteres.")

        # No vacío (por claridad, aunque la longitud ya lo cubre)
        if not password.strip():
            raise forms.ValidationError("La contraseña no puede estar vacía.")
        # Al menos una letra mayúscula
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("La contraseña debe contener al menos una letra mayúscula.")
        # Al menos un número
        if not re.search(r'\d', password):
            raise forms.ValidationError("La contraseña debe contener al menos un número.")
        # Al menos un carácter especial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError("La contraseña debe contener al menos un carácter especial.")
        # No espacios
        if re.search(r'\s', password):
            raise forms.ValidationError("La contraseña no puede contener espacios.")
        # No puede ser igual al nombre de usuario
        username = self.cleaned_data.get('username', '')
        if username and password.lower() == username.lower():
            raise forms.ValidationError("La contraseña no puede ser igual al nombre de usuario.")
        # No puede ser igual a la contraseña anterior
        if hasattr(self, 'instance') and self.instance and self.instance.password:
            if password == self.instance.password:
                raise forms.ValidationError("La nueva contraseña no puede ser igual a la anterior.")
        # No puede ser igual a la contraseña anterior (si existe)
        if hasattr(self, 'instance') and self.instance and self.instance.password:
            if password == self.instance.password:
                raise forms.ValidationError("La nueva contraseña no puede ser igual a la anterior.")
        # No puede contener el nombre de usuario
        if username and username.lower() in password.lower():
            raise forms.ValidationError("La contraseña no puede contener el nombre de usuario.")
        # No puede contener la palabra "password"
        if "password" in password.lower():
            raise forms.ValidationError("La contraseña no puede contener la palabra 'password'.")
        # No puede contener la palabra "user"
        if "user" in password.lower():
            raise forms.ValidationError("La contraseña no puede contener la palabra 'user'.")
        # No puede contener la palabra "admin"
        if "admin" in password.lower():
            raise forms.ValidationError("La contraseña no puede contener la palabra 'admin'.")
        # No puede contener la palabra "1234"
        if re.search(r'1234', password):
            raise forms.ValidationError("La contraseña no puede contener la secuencia '1234'.")
        # No puede contener la palabra "qwerty"
        if re.search(r'qwerty', password, re.IGNORECASE):
            raise forms.ValidationError("La contraseña no puede contener la secuencia 'qwerty'.")
        # No puede contener la palabra "abc"
        if re.search(r'abc', password, re.IGNORECASE):
            raise forms.ValidationError("La contraseña no puede contener la secuencia 'abc'.")
        # No puede contener la palabra "letmein"
        if re.search(r'letmein', password, re.IGNORECASE):
            raise forms.ValidationError("La contraseña no puede contener la secuencia   'letmein'.")
        # No puede contener la palabra "welcome"
        if re.search(r'welcome', password, re.IGNORECASE):
            raise forms.ValidationError("La contraseña no puede contener la secuencia 'welcome'.")
        # No puede contener la palabra "iloveyou"
        if re.search(r'iloveyou', password, re.IGNORECASE):
            raise forms.ValidationError("La contraseña no puede contener la secuencia 'iloveyou'.")
        return password
        
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'fecha_hora', 'servicios', 'direccion', 'cliente', 'categoria']
        widgets = {
            'fecha_hora': forms.DateTimeInput(
                attrs={
                    'class': 'form-control', 
                    'type': 'datetime-local'
                },
                
            ),
           
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
      
        
          # Elimina cualquier clase previa que pudiera venir de la definición del campo
        if 'class' in self.fields['servicios'].widget.attrs:
            del self.fields['servicios'].widget.attrs['class']
        
        # Asegurarse de que todos los campos sean requeridos
        for field in self.fields.values():
            field.required = True

        # Configurar helper de crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Configurar diseño del formulario
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6'),
                Column('fecha_hora', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Row(
                Column('cliente', css_class='form-group col-md-6'),
                Column('direccion', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            Div(
                'servicios', 
                css_class='form-group'
            ),
            Submit('submit', _('Guardar Evento'), css_class='btn btn-primary')
        )
        
        # Personalizar consulta de clientes
        self.fields['cliente'].queryset = Cliente.objects.all()
        self.fields['cliente'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido}"


MITSUBISHI_PAPER_CHOICES = [
    ('10x15', '10x15 (4x6")'),
    ('13x18', '13x18 (5x7")'),
    ('15x20', '15x20 (6x8")'),
    ('10x15x2_type1', '10x15x2 Type1 (4x6"x2)'),
    ('5x15x2_type1', '5x15x2 Type1 (2x6"x2)'),
    ('5x15x2_type2', '5x15x2 Type2 (2x6"x2)'),
    ('15x15', '15x15 (6x6")'),
    ('10x15_white', '10x15 (4x6") white border'),
    ('13x18_white', '13x18 (5x7") white border'),
    ('15x20_white', '15x20 (6x8") white border'),
    ('13x13', '13x13 (5x5")'),
]

class PhotoboothConfigForm(forms.ModelForm):
    """Formulario actualizado para configurar el photobooth con soporte USB"""
    
    class Meta:
        model = PhotoboothConfig
        fields = [
            # Campos básicos existentes
            'mensaje_bienvenida', 
            'imagen_fondo', 
            'color_texto', 
            'tamano_texto', 
            'tipo_letra',
            'plantilla_collage',
            
            # Campos de tiempo existentes
            'tiempo_entre_fotos',
            'tiempo_cuenta_regresiva',
            'tiempo_visualizacion_foto',
            
            # Campos de cámara existentes
            'nivel_iluminacion',
            'tipo_camara',
            'camera_id',
            'resolucion_camara',
            'iso_valor',
            
            # NUEVOS CAMPOS USB
            'usb_vendor_id',
            'usb_product_id', 
            'usb_serial_number',
            'usb_use_raw_mode',
            'usb_auto_download',
            'usb_delete_after_download',
            'usb_connection_timeout',
            'usb_capture_timeout',
            
            # Campos DSLR existentes
            'velocidad_obturacion',
            'apertura',
            'modo_disparo',
            'calidad_imagen',
            'modo_enfoque',
            
            # Campos de impresora existentes
            'printer_name',
            'paper_size',
            'copias_impresion',
            'calidad_impresion',
            'imprimir_automaticamente',
        ]
        
        widgets = {
            # Widgets existentes...
            'mensaje_bienvenida': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_fondo': forms.FileInput(attrs={'class': 'form-control'}),
            'color_texto': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'tamano_texto': forms.NumberInput(attrs={'class': 'form-control', 'min': '12', 'max': '72'}),
            'tipo_letra': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Arial', 'Arial'),
                ('Times New Roman', 'Times New Roman'),
                ('Courier New', 'Courier New'),
                ('Georgia', 'Georgia'),
                ('Verdana', 'Verdana'),
                ('Open Sans', 'Open Sans')
            ]),
            'plantilla_collage': forms.Select(attrs={'class': 'form-select'}),
            
            # Widgets para campos de tiempo
            'tiempo_entre_fotos': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '20'
            }),
            'tiempo_cuenta_regresiva': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '10'
            }),
            'tiempo_visualizacion_foto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '10'
            }),
            
            # Widgets para cámara
            'nivel_iluminacion': forms.NumberInput(attrs={
                'type': 'range',
                'class': 'form-range',
                'min': '0',
                'max': '100',
                'step': '5'
            }),
            'tipo_camara': forms.Select(attrs={
                'class': 'form-select',
                'id': 'tipo-camara',
                'onchange': 'updateCameraTypeSection()'
            }),
            'camera_id': forms.HiddenInput(attrs={'id': 'selected-camera-id'}),
            'resolucion_camara': forms.Select(attrs={'class': 'form-select'}),
            'iso_valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '100',
                'max': '3200'
            }),
            
            # NUEVOS WIDGETS USB
            'usb_vendor_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': 'Se detecta automáticamente'
            }),
            'usb_product_id': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': 'Se detecta automáticamente'
            }),
            'usb_serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
                'placeholder': 'Se detecta automáticamente'
            }),
            'usb_use_raw_mode': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'usb-raw-mode'
            }),
            'usb_auto_download': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'usb-auto-download'
            }),
            'usb_delete_after_download': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'usb-delete-after-download'
            }),
            'usb_connection_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'max': '60',
                'step': '5'
            }),
            'usb_capture_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '120',
                'step': '5'
            }),
            
            # Widgets DSLR existentes
            'velocidad_obturacion': forms.Select(attrs={'class': 'form-select'}),
            'apertura': forms.Select(attrs={'class': 'form-select'}),
            'modo_disparo': forms.Select(attrs={'class': 'form-select'}),
            'calidad_imagen': forms.Select(attrs={'class': 'form-select'}),
            'modo_enfoque': forms.Select(attrs={'class': 'form-select'}),
            
            # Widgets impresora existentes
            'printer_name': forms.Select(attrs={'class': 'form-select'}),
            'paper_size': forms.Select(attrs={'class': 'form-select'}),
            'copias_impresion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
            'calidad_impresion': forms.Select(attrs={'class': 'form-select'}),
            'imprimir_automaticamente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        printer_name = kwargs.pop('printer_name', None)
        evento = kwargs.pop('evento', None)
        super().__init__(*args, **kwargs)

        # Configurar plantillas por evento
        if evento:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.filter(evento=evento)
        else:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.all()
        
        self.fields['plantilla_collage'].empty_label = "-- Seleccionar plantilla --"
        
        # Configurar opciones del tipo de cámara
        self.fields['tipo_camara'].choices = [
            ('webcam', 'Cámara Web'),
            ('nikon_dslr', 'Nikon DSLR/Mirrorless'),
            ('usb_ptp', 'Cámara USB (PTP)'),
            ('canon_dslr', 'Canon DSLR'),
            ('sony_camera', 'Sony Camera'),
        ]
        
        # Configurar lista de impresoras (se llenará con JavaScript)
        self.fields['printer_name'].choices = [('', '-- Seleccionar impresora --')]
        
        # Personalizar opciones de papel según la impresora
        if printer_name and 'mitsubishi' in printer_name.lower():
            self.fields['paper_size'].choices = MITSUBISHI_PAPER_CHOICES
        else:
            self.fields['paper_size'].choices = [
                ('A4', 'A4'),
                ('Letter', 'Letter'),
                ('10x15', '10x15 (4x6")'),
                ('13x18', '13x18 (5x7")'),
                ('15x20', '15x20 (6x8")'),
                # ...otros tamaños estándar...
            ]
        
        # Organizar campos en grupos lógicos
        self.field_groups = {
            'basicos': [
                'mensaje_bienvenida', 'imagen_fondo', 'color_texto', 
                'tamano_texto', 'tipo_letra'
            ],
            'plantilla': ['plantilla_collage'],
            'tiempos': [
                'tiempo_entre_fotos', 'tiempo_cuenta_regresiva', 
                'tiempo_visualizacion_foto'
            ],
            'camara_basica': [
                'tipo_camara', 'camera_id', 'resolucion_camara', 
                'nivel_iluminacion', 'iso_valor'
            ],
            'usb_config': [
                'usb_vendor_id', 'usb_product_id', 'usb_serial_number',
                'usb_use_raw_mode', 'usb_auto_download', 'usb_delete_after_download',
                'usb_connection_timeout', 'usb_capture_timeout'
            ],
            'dslr_config': [
                'velocidad_obturacion', 'apertura', 'modo_disparo', 
                'calidad_imagen', 'modo_enfoque'
            ],
            'impresora': [
                'printer_name', 'paper_size', 'copias_impresion', 
                'calidad_impresion', 'imprimir_automaticamente'
            ],
        }
        
        # Añadir clases CSS condicionales
        self._add_conditional_classes()
    
    def _add_conditional_classes(self):
        """Añade clases CSS condicionales según el tipo de cámara"""
        # Los campos USB solo son visibles cuando tipo_camara es usb_ptp, canon_dslr o sony_camera
        usb_fields = [
            'usb_vendor_id', 'usb_product_id', 'usb_serial_number',
            'usb_use_raw_mode', 'usb_auto_download', 'usb_delete_after_download',
            'usb_connection_timeout', 'usb_capture_timeout'
        ]
        
        for field_name in usb_fields:
            if field_name in self.fields:
                widget_attrs = self.fields[field_name].widget.attrs
                widget_attrs['data-camera-types'] = 'usb_ptp,canon_dslr,sony_camera'
                widget_attrs['style'] = 'display: none;'  # Oculto por defecto
    
    def clean(self):
        """Validación personalizada del formulario"""
        cleaned_data = super().clean()
        tipo_camara = cleaned_data.get('tipo_camara')
        
        # Validaciones específicas para cámaras USB
        if tipo_camara in ['usb_ptp', 'canon_dslr', 'sony_camera']:
            connection_timeout = cleaned_data.get('usb_connection_timeout')
            capture_timeout = cleaned_data.get('usb_capture_timeout')
            
            if connection_timeout and capture_timeout:
                if connection_timeout >= capture_timeout:
                    raise forms.ValidationError(
                        "El timeout de captura debe ser mayor al timeout de conexión"
                    )
        
        # Validación de configuración DSLR
        if tipo_camara in ['nikon_dslr', 'canon_dslr']:
            required_dslr_fields = ['velocidad_obturacion', 'apertura', 'modo_disparo']
            for field in required_dslr_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"Este campo es requerido para cámaras DSLR")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guardado personalizado del formulario"""
        instance = super().save(commit=False)
        
        # Lógica especial para cámaras USB
        if instance.tipo_camara in ['usb_ptp', 'canon_dslr', 'sony_camera']:
            # Si no hay información USB y el tipo es USB, limpiar campos
            if not instance.usb_vendor_id and not instance.usb_product_id:
                instance.usb_connection_status = 'disconnected'
        
        if commit:
            instance.save()
        
        return instance

# Formulario adicional para selección rápida de cámara USB
class USBCameraSelectionForm(forms.Form):
    """Formulario para selección rápida de cámara USB detectada"""
    
    camera_selection = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Seleccionar cámara USB",
        required=True
    )
    
    auto_connect = forms.BooleanField(
        initial=True,
        required=False,
        label="Conectar automáticamente",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, available_cameras=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if available_cameras:
            choices = []
            for camera in available_cameras:
                camera_id = f"{camera['vendor_id']:04x}:{camera['product_id']:04x}"
                camera_label = f"{camera['model']}"
                if camera.get('serial_number'):
                    camera_label += f" (S/N: {camera['serial_number']})"
                choices.append((camera_id, camera_label))
            
            self.fields['camera_selection'].choices = choices
        else:
            self.fields['camera_selection'].choices = [
                ('', 'No se detectaron cámaras USB')
            ]
            self.fields['camera_selection'].widget.attrs['disabled'] = True
            self.fields['auto_connect'].widget.attrs['disabled'] = True

# Formulario para configuración avanzada USB
class USBCameraAdvancedForm(forms.Form):
    """Formulario para configuración avanzada de cámaras USB"""
    
    capture_format = forms.ChoiceField(
        choices=[
            ('jpeg_fine', 'JPEG Fine'),
            ('jpeg_normal', 'JPEG Normal'),
            ('raw', 'RAW'),
            ('raw_jpeg', 'RAW + JPEG'),
        ],
        initial='jpeg_fine',
        label="Formato de captura",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    auto_focus_before_capture = forms.BooleanField(
        initial=True,
        required=False,
        label="Enfoque automático antes de capturar",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    bracketing_enabled = forms.BooleanField(
        initial=False,
        required=False,
        label="Habilitar bracketing",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    bracketing_steps = forms.IntegerField(
        initial=3,
        min_value=3,
        max_value=9,
        label="Pasos de bracketing",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '3',
            'max': '9',
            'step': '2'
        }),
        help_text="Número de fotos en la secuencia de bracketing (impar)"
    )
    
    mirror_lockup = forms.BooleanField(
        initial=False,
        required=False,
        label="Bloqueo de espejo",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Reduce vibraciones en cámaras DSLR"
    )
    
    custom_white_balance = forms.IntegerField(
        required=False,
        min_value=2000,
        max_value=10000,
        label="Balance de blancos personalizado (K)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'ej: 5500'
        })
    )

    def clean_bracketing_steps(self):
        """Validar que los pasos de bracketing sean impares"""
        steps = self.cleaned_data.get('bracketing_steps')
        if steps and steps % 2 == 0:
            raise forms.ValidationError("Los pasos de bracketing deben ser un número impar")
        return steps

class CollageTemplateForm(forms.ModelForm):
    """Formulario para crear/editar plantillas de collage"""
    class Meta:
        model = CollageTemplate
        fields = ['nombre', 'descripcion', 'background_color', 'background_image', 'es_predeterminada']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'background_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'es_predeterminada': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    # Campo oculto para almacenar los datos de la plantilla en formato JSON
    template_data = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    def clean_template_data(self):
        """Validar que template_data es un JSON válido"""
        data = self.cleaned_data.get('template_data')
        if data:
            try:
                json.loads(data)
            except ValueError:
                raise forms.ValidationError("Los datos de la plantilla no son un JSON válido")
        return data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Guardar datos de la plantilla si están presentes
        template_data = self.cleaned_data.get('template_data')
        if template_data:
            instance.template_data = template_data
        
        if commit:
            instance.save()
        return instance
        
  
  
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

    
    
  #Formulario Django para añadir fotografía      

class AñadirFotoForm(forms.ModelForm):
    class Meta:
        model = Fotografia
        fields = ['img', 'descripcion', 'invitados']
        widgets = {
            
            'invitados': forms.CheckboxSelectMultiple(),
        }
    img = MultipleFileField(label='Seleccionar archivos', required=False)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'class':'descripcion','name':'descripcion', 'rows':3, 'cols':5}),label="Descripción")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invitados'].queryset = Invitado.objects.all()
        self.fields['invitados'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido}" if hasattr(obj, 'nombre') and hasattr(obj, 'apellido') else str(obj)


