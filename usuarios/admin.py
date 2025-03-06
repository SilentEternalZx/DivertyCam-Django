from django.contrib import admin
from .models import User, Rol, Permiso
from .models import Evento

admin.site.register(User)
admin.site.register(Rol)
admin.site.register(Permiso)



@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_hora', 'cliente', 'get_servicios_display_admin')
    list_filter = ('fecha_hora', 'servicios')
    search_fields = ('nombre', 'cliente__nombre', 'cliente__apellido', 'direccion')
    date_hierarchy = 'fecha_hora'
    
    def get_servicios_display_admin(self, obj):
        return ", ".join([str(s) for s in obj.get_servicios_display()])
    get_servicios_display_admin.short_description = 'Servicios'
