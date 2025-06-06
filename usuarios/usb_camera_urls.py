# usb_camera_urls.py
# URLs para funcionalidad de cámaras USB

from django.urls import path
from . import django_usb_camera

# URLs específicas para cámaras USB
usb_camera_patterns = [
    # Detección y conexión
    path('api/usb/cameras/detect/', django_usb_camera.detect_usb_cameras, name='detect_usb_cameras'),
    path('api/usb/cameras/connect/', django_usb_camera.connect_usb_camera, name='connect_usb_camera'),
    path('api/usb/cameras/disconnect/', django_usb_camera.disconnect_usb_camera, name='disconnect_usb_camera'),
    
    # Captura y control
    path('api/usb/cameras/capture/', django_usb_camera.capture_usb_photo, name='capture_usb_photo'),
    path('api/usb/cameras/setting/set/', django_usb_camera.set_usb_camera_setting, name='set_usb_camera_setting'),
    path('api/usb/cameras/setting/get/', django_usb_camera.get_usb_camera_setting, name='get_usb_camera_setting'),
    
    # Estado y monitoreo
    path('api/usb/cameras/status/', django_usb_camera.get_camera_status, name='get_camera_status'),
]

# Añadir estas URLs al urls.py principal:
"""
# En tu urls.py principal, añade:

from django.urls import path, include
from . import usb_camera_urls

urlpatterns = [
    # ... tus URLs existentes
    
    # URLs para cámaras USB
    path('', include(usb_camera_urls.usb_camera_patterns)),
    
    # ... resto de URLs
]
"""