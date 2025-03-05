
from django import forms
from .models import Cliente, Fotografia, User
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm

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