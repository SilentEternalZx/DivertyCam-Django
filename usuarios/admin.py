from django.contrib import admin
from .models import*

admin.site.register(User)
admin.site.register(Invitado)
admin.site.register(Fotografia)
admin.site.register(Permiso)
admin.site.register(Rol)