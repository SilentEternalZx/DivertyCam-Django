from django.urls import path
from . import views

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("register", views.register_view, name="register"),
    path("logout", views.logout_view, name="logout"),
    path("permisos", views.obtener_permisos_usuario, name="obtener_permisos"),
    path("asignar-rol/<int:usuario_id>/<int:rol_id>", views.asignar_rol_usuario, name="asignar_rol"),
    path("", views.index, name="index")
]
