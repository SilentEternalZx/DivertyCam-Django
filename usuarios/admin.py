from django.contrib import admin
from .models import*

#Registrar modelos
admin.site.register(User)

admin.site.register(CategoriaEvento)
admin.site.register(Invitado)
admin.site.register(Fotografia)




