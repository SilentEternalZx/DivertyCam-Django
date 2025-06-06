from django.contrib import admin
from .models import*
from django.contrib.auth import get_user_model
from .forms import *

# ModelAdmin personalizado para User
class UserAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        # Si el usuario es superusuario, no permitir eliminar
        if obj and getattr(obj, 'is_superuser', False):
            return False
        return super().has_delete_permission(request, obj)

    def delete_model(self, request, obj):
        # Seguridad extra: nunca eliminar superusuarios
        if getattr(obj, 'is_superuser', False):
            return
        super().delete_model(request, obj)

#Registrar modelos


admin.site.register(Invitado)
admin.site.register(CategoriaEvento)
admin.site.register(Cliente)
admin.site.register(Evento)










