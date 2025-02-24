from django.contrib import admin
from .models import User, Rol, Permiso

admin.site.register(User)
admin.site.register(Rol)
admin.site.register(Permiso)