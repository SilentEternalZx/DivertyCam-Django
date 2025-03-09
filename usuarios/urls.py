from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from . import admin


#Urls
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.vista_login, name="login"),
    path("register", views.register_view, name="register"),
    path("logout", views.vista_logout, name="logout"),
    path("descargar_foto/<int:evento_id>", views.descargar_foto, name="descargar_foto"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"), 
    path('cliente_list', views.ClienteListView.as_view(), name='cliente_list'),
    path('<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    path("subir_foto/", views.subir_foto, name="subir_foto"),
    path("fotos/", views.lista_fotos, name="lista_fotos"),
    path("publicar_foto/<int:foto_id>/", views.publicar_foto_facebook, name="publicar_foto"),
    path('evento_list', views.EventoListView.as_view(), name='evento_list'),
    path('evento_list/nuevo/', views.EventoCreateView.as_view(), name='evento_create'),
    path('evento_list/<int:pk>/', views.EventoDetailView.as_view(), name='evento_detail'),
    path('evento_list/<int:pk>/editar/', views.EventoUpdateView.as_view(), name='evento_update'),
    path('evento_list/<int:pk>/eliminar/', views.EventoDeleteView.as_view(), name='evento_delete'),
    path('añadir_foto/<int:evento_id>', views.añadir_foto, name="añadir_foto"),
    path('mis_eventos', views.mis_eventos, name="mis_eventos")
  
   
]