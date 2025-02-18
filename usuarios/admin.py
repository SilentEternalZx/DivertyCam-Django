from django.contrib import admin
from .models import User, Rol, Permiso

# Configuración del modelo User en el admin
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email")
    search_fields = ("username", "email")
    filter_horizontal = ("roles",)

# Configuración del modelo Rol en el admin
@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)
    filter_horizontal = ("permisos",)

# Configuración del modelo Permiso en el admin
@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado", "fecha_creacion")
    search_fields = ("nombre",)
