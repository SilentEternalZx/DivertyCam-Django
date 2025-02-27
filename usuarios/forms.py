
from django import forms
from .models import Cliente
from django.utils.translation import gettext_lazy as _

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