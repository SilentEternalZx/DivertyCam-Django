
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from .models import Evento, Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'cedula', 'fechaNacimiento', 
                  'direccion', 'correo', 'telefono']
        widgets = {
            'fechaNacimiento': forms.DateInput(attrs={'type': 'date'}),
            'direccion': forms.Textarea(attrs={'rows': 3}),
        }
        
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        # Aquí puedes agregar validaciones específicas para la cédula
        # dependiendo del país o región
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