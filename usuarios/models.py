from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.contrib.auth.models import Group, Permission

# Modelo de Usuario personalizado
class User(AbstractUser):
    pass
# Modelo de Roles
class Rol(Group):
    pass

# Modelo de Permisos
class Permiso(Permission):
    pass
