
import json
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from .models import CollageTemplate, Evento, Cliente, Configurar_Photobooth, PhotoboothConfig


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'cedula', 'fechaNacimiento', 
                  'direccion', 'correo', 'telefono']
        widgets = {
            'fechaNacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
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
        # Aquí puedes agregar validaciones específicas para la cédula
        return cedula
        
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        # Validaciones adicionales de correo si es necesario
        return correo

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre', 'fecha_hora', 'servicios', 'direccion', 'cliente']
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
                  'tipo_letra', 'max_fotos', 'permitir_personalizar']
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
            'max_fotos': forms.Select(attrs={'class': 'form-select'}),
            'permitir_personalizar': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class PhotoboothConfigForm(forms.ModelForm):
    """Formulario para configurar el photobooth"""
    class Meta:
        model = PhotoboothConfig
        fields = [
            'mensaje_bienvenida', 'imagen_fondo', 'color_texto', 
            'tamano_texto', 'tipo_letra', 'max_fotos', 
            'permitir_personalizar', 'plantilla_collage'
        ]
        widgets = {
            'mensaje_bienvenida': forms.TextInput(attrs={'class': 'form-control'}),
            'color_texto': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'tamano_texto': forms.NumberInput(attrs={'class': 'form-control', 'min': '12', 'max': '72'}),
            'tipo_letra': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('Arial', 'Arial'),
                ('Helvetica', 'Helvetica'),
                ('Times New Roman', 'Times New Roman'),
                ('Courier New', 'Courier New'),
                ('Verdana', 'Verdana')
            ]),
            'max_fotos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'permitir_personalizar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'plantilla_collage': forms.Select(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        evento = kwargs.pop('evento', None)
        super().__init__(*args, **kwargs)

        # Añadir depuración
        print(f"Inicializando formulario con evento: {evento}")
        if self.instance and self.instance.pk:
            print(f"Instancia existente, plantilla: {self.instance.plantilla_collage}")
        
        # Filtrar plantillas por evento si se proporciona
        if evento:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.filter(evento=evento)
        else:
            self.fields['plantilla_collage'].queryset = CollageTemplate.objects.all()
        
        # Añadir opción vacía
        self.fields['plantilla_collage'].empty_label = "-- Seleccionar plantilla --"

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
