# windows_camera_urls.py
# URLs específicas para cámaras Windows

from django.urls import path
from . import django_windows_camera

# URLs para cámaras Windows
windows_camera_patterns = [
    # Detección y conexión Windows
    path('api/windows/cameras/detect/', django_windows_camera.detect_windows_cameras, name='detect_windows_cameras'),
    path('api/windows/cameras/connect/', django_windows_camera.connect_windows_camera, name='connect_windows_camera'),
    path('api/windows/cameras/disconnect/', django_windows_camera.disconnect_windows_camera, name='disconnect_windows_camera'),
    
    # Captura y control Windows
    path('api/windows/cameras/capture/', django_windows_camera.capture_windows_photo, name='capture_windows_photo'),
    path('api/windows/cameras/setting/set/', django_windows_camera.set_windows_camera_setting, name='set_windows_camera_setting'),
    path('api/windows/cameras/setting/get/', django_windows_camera.get_windows_camera_setting, name='get_windows_camera_setting'),
    
    # Estado Windows
    path('api/windows/cameras/status/', django_windows_camera.get_windows_camera_status, name='get_windows_camera_status'),
]

"""
Para integrar en tu urls.py principal:

from django.urls import path, include
from . import windows_camera_urls

urlpatterns = [
    # ... tus URLs existentes
    
    # URLs para cámaras Windows
    path('', include(windows_camera_urls.windows_camera_patterns)),
    
    # ... resto de URLs
]
"""