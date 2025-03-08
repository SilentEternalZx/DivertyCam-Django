from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from multiselectfield import MultiSelectField


# Modelo de Usuario personalizado
class User(AbstractUser):
   pass




class Invitado(models.Model):
    nombre=models.CharField(max_length=20)
    telefono=models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return f'{self.nombre} {self.telefono}'
    


class Fotografia(models.Model):
    
    img=models.ImageField(null=True,blank=True, upload_to="list_image/")
    descripcion=models.TextField()
    invitado=models.ForeignKey(Invitado, related_name="fotografias", on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.descripcion} {self.invitado}'
    

class Cliente(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name=_("Nombre"),
        help_text=_("Nombre del cliente")
    )
    
    apellido = models.CharField(
        max_length=100,
        verbose_name=_("Apellido"),
        help_text=_("Apellido del cliente")
    )
    
    cedula = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Cédula"),
        help_text=_("Número de cédula o documento de identidad"),
        db_index=True
    )
    
    fechaNacimiento = models.DateField(
        verbose_name=_("Fecha de Nacimiento"),
        help_text=_("Fecha de nacimiento del cliente")
    )
    
    direccion = models.CharField(
        max_length=255,
        verbose_name=_("Dirección"),
        help_text=_("Dirección completa del cliente")
    )
    
    correo = models.EmailField(
        unique=True,
        verbose_name=_("Correo Electrónico"),
        help_text=_("Correo electrónico del cliente"),
        db_index=True
    )
    
    telefono_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos.")
    )
    
    telefono = models.CharField(
        validators=[telefono_regex],
        max_length=17,
        verbose_name=_("Teléfono"),
        help_text=_("Número de teléfono del cliente")
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
        verbose_name = _("Cliente")
        verbose_name_plural = _("Clientes")
        ordering = ["apellido", "nombre"]
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['correo']),
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
        SearchVector('correo', weight='B') +
        SearchVector('direccion', weight='C')
    )
