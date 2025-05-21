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
        fields = ['nombre','apellido', 'cedula', 'fechaNacimiento', 
                  'direccion', 'correo', 'telefono', 'usuario']
        widgets = {
            'fechaNacimiento': forms.DateInput(attrs={'type': 'date', 'class':'apellido'}),
            
            
            
        }
    def clean_fechaNacimiento(self):
        fechaNacimiento = self.cleaned_data.get('fechaNacimiento')
        
        if fechaNacimiento:
            # Importar datetime
            import datetime
            
            # Calcular la edad
            hoy = datetime.date.today()
            edad = hoy.year - fechaNacimiento.year - ((hoy.month, hoy.day) < (fechaNacimiento.month, fechaNacimiento.day))
            
            # Verificar si es menor de 18 años
            if edad < 18:
                raise forms.ValidationError("El cliente debe ser mayor de edad (18 años o más).")
        
        return fechaNacimiento
        
        
        
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        # Validaciones adicionales de cédula si es necesario
        if not cedula.isdigit():
            raise forms.ValidationError("La cédula debe contener solo números.")
        if not (6 <= len(cedula) <= 10):
            raise forms.ValidationError("La cédula debe tener entre 6 y 10 dígitos.")
        return cedula
        
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        # Validaciones adicionales de correo si es necesario
        return correo


class FotografiaForm(forms.ModelForm):
    class Meta:
        model = Fotografia
        fields = ['img', 'descripcion', 'invitado']
        
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
                }
            ),
            'servicios': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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

class Configurar_PhotoboothForm(forms.ModelForm):
    class Meta:
        model = Configurar_Photobooth
        fields = ['mensaje_bienvenida', 'imagen_fondo', 'color_texto', 'tamano_texto', 
                  'tipo_letra', 'resolucion_camara', 'balance_blancos']
        widgets = {
            'mensaje_bienvenida': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_fondo': forms.FileInput(attrs={'class': 'form-control'}),
            'color_texto': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'tamano_texto': forms.NumberInput(attrs={'class': 'form-control', 'min': '12', 'max': '72'}),
            'tipo_letra': forms.Select(attrs={'class': 'form-select'}, choices=(
                ('Arial', 'Arial'),
                ('Times New Roman', 'Times New Roman'),
                ('Courier New', 'Courier New'),
                ('Georgia', 'Georgia'),
                ('Verdana', 'Verdana'),
                ('Open Sans', 'Open Sans')
            )),
            'resolucion_camara': forms.Select(attrs={'class': 'form-select', 'id': 'camera-resolution'}),
            'balance_blancos': forms.Select(attrs={'class': 'form-select', 'id': 'white-balance'}),
            'permitir_personalizar': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class PhotoboothConfigForm(forms.ModelForm):
    """Formulario para configurar el photobooth"""
    class Meta:
        model = PhotoboothConfig
        fields = [
            # Campos básicos
            'mensaje_bienvenida', 
            'imagen_fondo', 
            'color_texto', 
            'tamano_texto', 
            'tipo_letra',
            'plantilla_collage',
            # Nuevos campos de tiempo
            'tiempo_entre_fotos',
            'tiempo_cuenta_regresiva',
            'tiempo_visualizacion_foto',
            # Configuración de cámara
            'camera_id',
            'resolucion_camara',
            'balance_blancos',
            'iso_valor',
            # Configuración de impresora
            'printer_name',
            'paper_size',
            'copias_impresion',
            'calidad_impresion',
            'imprimir_automaticamente',
        ]
        widgets = {
            # Widgets para campos existentes
            'mensaje_bienvenida': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_fondo': forms.FileInput(attrs={'class': 'form-control'}),
            'color_texto': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'tamano_texto': forms.NumberInput(attrs={'class': 'form-control', 'min': '12', 'max': '72'}),
            'tipo_letra': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Arial', 'Arial'),
                ('Helvetica', 'Helvetica'),
                ('Times New Roman', 'Times New Roman'),
                ('Courier New', 'Courier New'),
                ('Verdana', 'Verdana'),
                ('Open Sans', 'Open Sans'),
                ('Roboto', 'Roboto'),
                ('Montserrat', 'Montserrat'),
            ]),
            'plantilla_collage': forms.Select(attrs={'class': 'form-select'}),
            
            # Widgets para nuevos campos de tiempo
            'tiempo_entre_fotos': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '20', 
                'id': 'tiempo-entre-fotos'
            }),
            'tiempo_cuenta_regresiva': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '10', 
                'id': 'tiempo-cuenta-regresiva'
            }),
            'tiempo_visualizacion_foto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1', 
                'max': '10', 
                'id': 'tiempo-visualizacion-foto'
            }),
            
            # Widgets para configuración de cámara
            'camera_id': forms.HiddenInput(attrs={'id': 'selected-camera-id'}),
            'resolucion_camara': forms.Select(attrs={
                'class': 'form-select',
                'id': 'camera-resolution'
            }),
            'balance_blancos': forms.Select(attrs={
                'class': 'form-select',
                'id': 'white-balance'
            }),
            'iso_valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '100',
                'max': '3200',
                'id': 'iso-valor'
            }),
            
            # Widgets para configuración de impresora
            'printer_name': forms.Select(attrs={
                'class': 'form-select',
                'id': 'printer-select'
            }),
            'paper_size': forms.Select(attrs={
                'class': 'form-select',
                'id': 'paper-size'
            }),
            'copias_impresion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'id': 'copias-impresion'
            }),
            'calidad_impresion': forms.Select(attrs={
                'class': 'form-select',
                'id': 'calidad-impresion'
            }),
            'imprimir_automaticamente': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'imprimir-automaticamente'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        evento = kwargs.pop('evento', None)
        super().__init__(*args, **kwargs)

        # Filtrar plantillas por evento si se proporciona
        if evento:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.filter(evento=evento)
        else:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.all()
        
        # Añadir opción vacía para el selector de plantillas
        self.fields['plantilla_collage'].empty_label = "-- Seleccionar plantilla --"
        
        # Para la selección de impresora, necesitamos obtener la lista de impresoras
        # Este valor se llenará con JavaScript cuando se cargue la página
        self.fields['printer_name'].choices = [('', '-- Seleccionar impresora --')]
        
        # Poner campos en grupos lógicos para una mejor organización en la plantilla
        self.field_groups = {
            'basicos': ['mensaje_bienvenida', 'imagen_fondo', 'color_texto', 'tamano_texto', 'tipo_letra'],
            'plantilla': ['plantilla_collage'],
            'tiempos': ['tiempo_entre_fotos', 'tiempo_cuenta_regresiva', 'tiempo_visualizacion_foto'],
            'camara': ['camera_id', 'resolucion_camara', 'balance_blancos', 'iso_valor'],
            'impresora': ['printer_name', 'paper_size', 'copias_impresion', 'calidad_impresion', 'imprimir_automaticamente'],
        }

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
        
  
  
  

    
    
  #Formulario Django para añadir fotografía      
class AñadirFotoForm(forms.Form):
    img=forms.ImageField(widget=forms.ClearableFileInput(attrs={'class':'img'}),label="Imagen")
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'class':'descripcion','name':'descripcion', 'rows':3, 'cols':5}),label="Descripción")



