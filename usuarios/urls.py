from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import admin,views
from .views import CustomPasswordResetView, capture_nikon_photo, configure_nikon_camera, connect_nikon_camera, detect_nikon_cameras, nikon_liveview_stream
from .views import video_feed, index
from .views import list_printers, print_document
from django.urls import path, include
from . import usb_camera_urls

from . import windows_camera_urls


try:
    from .windows_camera_urls import windows_camera_patterns
    CAMERA_URLS_AVAILABLE = True
except ImportError:
    CAMERA_URLS_AVAILABLE = False
    windows_camera_patterns = []

#Urls
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.vista_login, name="login"),
    path("register", views.register_view, name="register"),
    path("logout", views.vista_logout, name="logout"),
    path("descargar_foto/<int:evento_id>", views.descargar_foto, name="descargar_foto"),
    path("password_reset/", CustomPasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"), 
    path('cliente_list', views.ClienteListView.as_view(), name='cliente_list'),
    path('<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('cliente/nuevo/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    path('<int:pk>/activar/', views.ClienteActivarView.as_view(), name='cliente_activar'),
    path('<int:pk>/inactivar/', views.ClienteInactivarView.as_view(), name='cliente_inactivar'),
    path("subir_foto/", views.subir_foto, name="subir_foto"),
    path("fotos/", views.lista_fotos, name="lista_fotos"),
    path("categorias/", views.listar_categorias, name="listar_categorias"),
    path("eventos/<int:categoria_id>/", views.listar_eventos, name="listar_eventos"),
    path("fotos/<int:evento_id>/", views.listar_fotos_evento, name="listar_fotos_evento"),
    path("publicar_album/<int:evento_id>/", views.publicar_album_facebook, name="publicar_album_facebook"),
    path("publicar_foto/<int:foto_id>/", views.publicar_foto_facebook, name="publicar_foto"),
    path('evento_list', views.EventoListView.as_view(), name='evento_list'),
    path('evento_list/nuevo/', views.EventoCreateView.as_view(), name='evento_create'),
    path('evento_list/<int:pk>/', views.EventoDetailView.as_view(), name='evento_detail'),
    path('evento_list/<int:pk>/editar/', views.EventoUpdateView.as_view(), name='evento_update'),
    path('evento_list/<int:pk>/eliminar/', views.EventoDeleteView.as_view(), name='evento_delete'),
    path('evento/<int:evento_id>/photobooth/configurar/', views.configurar_photobooth, name='configurar_photobooth'),
    path('evento/<int:evento_id>/photobooth/preview/', views.preview_photobooth, name='preview_photobooth'),
    path('evento/<int:evento_id>/photobooth/launch/', views.launch_photobooth, name='launch_photobooth'),
    #path('evento/<int:evento_id>/photobooth/collage/', views.photobooth_collage, name='photobooth_collage'),
    path('evento/<int:evento_id>/collage/plantillas/', views.template_list, name='template_list'),
    path('evento/<int:evento_id>/collage/editor/', views.template_editor, name='template_editor'),
    path('evento/<int:evento_id>/collage/editor/<str:template_id>/', views.template_editor, name='template_editor_edit'),
    path('evento/<int:evento_id>/collage/template/<str:template_id>/delete/', views.template_delete, name='template_delete'),

     # APIs para plantillas
    path('api/collage/save-template/', views.save_template, name='save_template'),
    path('api/collage/template/<str:template_id>/', views.get_template_data, name='get_template_data'),
    
    # Sesión de fotos
    path('evento/<int:evento_id>/collage/sesion/<str:template_id>/', views.start_session, name='start_session'),
    path('api/collage/save-photo/', views.save_session_photo, name='save_session_photo'),
    path('collage/session/<str:session_id>/result/', views.session_result, name='session_result'),
    
    # APIs para collage final
    path('api/collage/update-print-count/', views.update_print_count, name='update_print_count'),
    path('api/collage/send-whatsapp/', views.send_whatsapp, name='send_whatsapp'),
    path('añadir_foto/<int:evento_id>', views.añadir_foto, name="añadir_foto"),
  
    path("verificar_usuario/", views.verificar_usuario, name="verificar_usuario"),
    path("verificar_email/", views.verificar_email, name="verificar_email"),

    
    path('eventos/<int:evento_id>/photobooth/', views.launch_photobooth, name='launch_photobooth'),
    path('eventos/<int:evento_id>/photobooth/template/<str:template_id>/session/', views.start_session, name='start_session'),
    path('photobooth/save-photo/', views.save_session_photo, name='save_session_photo'),
    path('photobooth/session/<str:session_id>/result/', views.session_result, name='session_result'),
    path('photobooth/update-print-count/', views.update_print_count, name='update_print_count'),
    path('camaras', views.camaras, name='camaras'),
    path('camara/video_feed/', views.video_feed, name='video_feed'),
    path('añadir_foto/<int:evento_id>', views.añadir_foto, name="añadir_foto"),
    path('mis_eventos', views.mis_eventos, name="mis_eventos"),
    path("verificar_usuario/", views.verificar_usuario, name="verificar_usuario"),
    path("verificar_email/", views.verificar_email, name="verificar_email"),
    path('camaras', views.camaras, name='camaras'),
    path('camara/video_feed/', views.video_feed, name='video_feed'),
    path('capture', views.capture, name='capture'),
    path('set_iso', views.set_iso, name='set_iso'),
    path('set_white_balance/', views.set_white_balance, name='set_white_balance'),
    path('switch_camera', views.switch_camera, name='switch_camera'),
    path('impresoras/<int:evento_id>', views.impresoras, name='impresoras'),
    path('list_printers/', views.list_printers, name='list_printers'),
    path('print_document/', views.print_document, name='print_document'),
    path('photobooth/save_collage/', views.save_collage, name='save_collage'),
    # APIs para control de Nikon
    path('api/nikon/detect/', detect_nikon_cameras, name='detect_nikon_cameras'),
    path('api/nikon/connect/', connect_nikon_camera, name='connect_nikon_camera'),
    path('api/nikon/configure/', configure_nikon_camera, name='configure_nikon_camera'),
    path('api/nikon/capture/', capture_nikon_photo, name='capture_nikon_photo'),
    path('api/nikon/liveview/', nikon_liveview_stream, name='nikon_liveview_stream'),
    # URLs para cámaras USB
    path('', include(usb_camera_urls.usb_camera_patterns)),
    # URLs para cámaras Windows
    path('', include(windows_camera_urls.windows_camera_patterns)),
    # URLs para sistema de WhatsApp móvil
    path('api/whatsapp/send-to-mobile/', views.send_to_mobile_device, name='send_to_mobile_device'),
    path('api/whatsapp/transfer-status/', views.check_mobile_transfer_status, name='check_mobile_transfer_status'),
    path('api/whatsapp/device-status/', views.get_device_status, name='get_device_status'),
    path('api/whatsapp/save-data/', views.save_whatsapp_data, name='save_whatsapp_data'),
    
]

# Añadir URLs de cámaras si están disponibles
if CAMERA_URLS_AVAILABLE:
    urlpatterns.extend(windows_camera_patterns)
