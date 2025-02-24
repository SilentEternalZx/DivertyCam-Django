from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.utils.timezone import now

# Modelo de Usuario personalizado
class User(AbstractUser):
   pass


class Permiso(Permission):
    pass

class Rol(Group):
    pass


class Invitado(models.Model):
    nombre=models.CharField(max_length=20)
    telefono=models.CharField(max_length=20)
    
    def __str__(self):
        return f'{self.nombre} {self.telefono}'
    


class Fotografia(models.Model):
    
    img=models.ImageField(null=True,blank=True, upload_to="list_image/")
    descripcion=models.TextField(max_length=100)
    invitado=models.ForeignKey(Invitado, related_name="fotografias", on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.descripcion} {self.invitado}'
    
    
