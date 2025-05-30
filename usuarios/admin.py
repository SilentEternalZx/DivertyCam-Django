from django.contrib import admin
from .models import*
from django.contrib.auth import get_user_model
from .forms import EventoAdminForm

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
admin.site.register(User, UserAdmin)

admin.site.register(Invitado)
admin.site.register(Fotografia)
admin.site.register(CategoriaEvento)
admin.site.register(Cliente)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    form = EventoAdminForm
    list_display = ('nombre', 'fecha_hora', 'cliente', 'get_servicios_display_admin')
    list_filter = ('fecha_hora', 'servicios')
    search_fields = ('nombre', 'cliente__nombre', 'cliente__apellido', 'direccion')
    date_hierarchy = 'fecha_hora'

    def get_servicios_display_admin(self, obj):
        return ", ".join([str(s) for s in obj.get_servicios_display()])
    get_servicios_display_admin.short_description = 'Servicios'


