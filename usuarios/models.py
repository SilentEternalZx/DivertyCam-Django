from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

# Modelo de Usuario personalizado
class User(AbstractUser):
    roles = models.ManyToManyField("Rol", blank=True)

    def __str__(self):
        return self.username

# Modelo de Roles
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    permisos = models.ManyToManyField("Permiso", blank=True)

    def __str__(self):
        return self.nombre

# Modelo de Permisos
class Permiso(models.Model):
    nombre = models.CharField(max_length=40, unique=True)
    fecha_creacion = models.DateTimeField(default=now)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {'Activo' if self.estado else 'Inactivo'}"
