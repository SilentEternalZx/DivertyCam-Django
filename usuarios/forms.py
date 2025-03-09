
from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Div
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'cedula', 'fechaNacimiento', 
                  'direccion', 'correo', 'telefono', 'usuario']
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


class FotografiaForm(forms.ModelForm):
    class Meta:
        model = Fotografia
        fields = ['img', 'descripcion', 'invitado']
        
class RegistroForm(UserCreationForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        max_length=20,  # 📌 Máximo 20 caracteres
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
        
  
  #Formulario Django para añadir fotografía      
class AñadirFotoForm(forms.Form):
    img=forms.ImageField(widget=forms.ClearableFileInput)
    descripcion = forms.CharField(widget=forms.Textarea(attrs={'name':'descripcion', 'rows':3, 'cols':5}))
    
    