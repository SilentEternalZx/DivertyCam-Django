# create_camera_files.py
# Script para crear los archivos necesarios en el orden correcto

import os

def create_file_with_content(filepath, content):
    """Crea un archivo con el contenido especificado"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Creado: {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error creando {filepath}: {e}")
        return False

def create_camera_files():
    """Crea todos los archivos necesarios para cámaras USB"""
    
    # Directorio base (ajustar según tu estructura)
    base_dir = "usuarios"  # Cambiar por tu directorio de app
    
    if not os.path.exists(base_dir):
        print(f"❌ Directorio {base_dir} no existe. Ajusta la ruta en el script.")
        return False
    
    print(f"📁 Creando archivos en: {base_dir}")
    
    # 1. camera_usb_detector.py (básico para evitar errores de importación)
    detector_content = '''# camera_usb_detector.py
# Detector USB básico para evitar errores de importación

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class USBCameraDetector:
    """Detector básico de cámaras USB"""
    
    def __init__(self):
        self.detected_cameras = []
        
    def scan_for_cameras(self) -> List[Dict]:
        """Escanea puertos USB buscando cámaras conectadas"""
        cameras = []
        
        try:
            # Implementación básica - se expandirá después
            logger.info("Escaneando cámaras USB...")
            # Por ahora retorna lista vacía para evitar errores
            
        except Exception as e:
            logger.error(f"Error al escanear dispositivos USB: {str(e)}")
            
        self.detected_cameras = cameras
        return cameras
    
    def get_cameras_by_vendor(self, vendor_name: str) -> List[Dict]:
        """Filtra cámaras por fabricante"""
        return [cam for cam in self.detected_cameras 
                if cam.get('vendor_name', '').lower() == vendor_name.lower()]

# Función simple para testear
if __name__ == "__main__":
    detector = USBCameraDetector()
    cameras = detector.scan_for_cameras()
    print(f"Detectadas {len(cameras)} cámaras")
'''
    
    # 2. windows_ptp_controller.py (básico)
    controller_content = '''# windows_ptp_controller.py
# Controlador PTP básico para Windows

import os
import sys
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class WindowsPTPController:
    """Controlador PTP básico para Windows"""
    
    def __init__(self):
        self.is_windows = sys.platform.startswith('win')
        self.connected_camera = None
        
    def detect_cameras(self) -> List[Dict]:
        """Detecta cámaras disponibles"""
        cameras = []
        
        if not self.is_windows:
            return cameras
            
        try:
            # Implementación básica - se expandirá después
            logger.info("Detectando cámaras Windows...")
            
        except Exception as e:
            logger.error(f"Error detectando cámaras: {e}")
        
        return cameras
    
    def connect_camera(self, camera_id: str, camera_type: str = None) -> bool:
        """Conecta con una cámara"""
        try:
            logger.info(f"Conectando con cámara: {camera_id}")
            # Implementación básica
            return True
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            return False
    
    def disconnect_camera(self):
        """Desconecta la cámara"""
        self.connected_camera = None
    
    def capture_image(self) -> Optional[str]:
        """Captura una imagen"""
        try:
            logger.info("Capturando imagen...")
            # Implementación básica
            return None
        except Exception as e:
            logger.error(f"Error capturando: {e}")
            return None
    
    def cleanup(self):
        """Limpia recursos"""
        self.disconnect_camera()
'''
    
    # 3. django_windows_camera.py (básico)
    django_content = '''# django_windows_camera.py
# Integración Django básica para cámaras Windows

import json
import logging
from typing import Dict, List
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

logger = logging.getLogger(__name__)

# Importar controlador (con manejo de errores)
try:
    from .windows_ptp_controller import WindowsPTPController
    CONTROLLER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Controlador Windows no disponible: {e}")
    CONTROLLER_AVAILABLE = False

class DjangoWindowsCameraManager:
    """Manager básico para cámaras Windows"""
    
    def __init__(self):
        self.controller = None
        if CONTROLLER_AVAILABLE:
            try:
                self.controller = WindowsPTPController()
            except Exception as e:
                logger.error(f"Error inicializando controlador: {e}")
    
    def is_available(self) -> bool:
        return CONTROLLER_AVAILABLE and self.controller is not None
    
    def get_available_cameras(self) -> List[Dict]:
        if not self.is_available():
            return []
        return self.controller.detect_cameras()

# Instancia global
windows_camera_manager = DjangoWindowsCameraManager()

# ==================== VISTAS DJANGO ====================

@csrf_exempt
@require_GET
def detect_windows_cameras(request):
    """API básica para detectar cámaras Windows"""
    try:
        cameras = windows_camera_manager.get_available_cameras()
        return JsonResponse({
            'success': True,
            'cameras': cameras,
            'count': len(cameras),
            'platform': 'Windows'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'cameras': [],
            'count': 0
        })

@csrf_exempt
@require_POST
def connect_windows_camera(request):
    """API básica para conectar cámara"""
    return JsonResponse({
        'success': False,
        'error': 'Funcionalidad en desarrollo'
    })

@csrf_exempt
@require_POST
def disconnect_windows_camera(request):
    """API básica para desconectar cámara"""
    return JsonResponse({
        'success': False,
        'error': 'Funcionalidad en desarrollo'
    })

@csrf_exempt
@require_POST
def capture_windows_photo(request):
    """API básica para capturar foto"""
    return JsonResponse({
        'success': False,
        'error': 'Funcionalidad en desarrollo'
    })

@csrf_exempt
@require_POST
def set_windows_camera_setting(request):
    """API básica para configurar cámara"""
    return JsonResponse({
        'success': False,
        'error': 'Funcionalidad en desarrollo'
    })

@csrf_exempt
@require_GET
def get_windows_camera_setting(request):
    """API básica para obtener configuración"""
    return JsonResponse({
        'success': False,
        'error': 'Funcionalidad en desarrollo'
    })

@csrf_exempt
@require_GET
def get_windows_camera_status(request):
    """API básica para obtener estado"""
    return JsonResponse({
        'success': True,
        'is_available': windows_camera_manager.is_available(),
        'platform': 'Windows'
    })
'''
    
    # 4. windows_camera_urls.py (básico)
    urls_content = '''# windows_camera_urls.py
# URLs básicas para cámaras Windows

from django.urls import path
from . import django_windows_camera

# URLs para cámaras Windows (básicas)
windows_camera_patterns = [
    path('api/windows/cameras/detect/', django_windows_camera.detect_windows_cameras, name='detect_windows_cameras'),
    path('api/windows/cameras/connect/', django_windows_camera.connect_windows_camera, name='connect_windows_camera'),
    path('api/windows/cameras/disconnect/', django_windows_camera.disconnect_windows_camera, name='disconnect_windows_camera'),
    path('api/windows/cameras/capture/', django_windows_camera.capture_windows_photo, name='capture_windows_photo'),
    path('api/windows/cameras/setting/set/', django_windows_camera.set_windows_camera_setting, name='set_windows_camera_setting'),
    path('api/windows/cameras/setting/get/', django_windows_camera.get_windows_camera_setting, name='get_windows_camera_setting'),
    path('api/windows/cameras/status/', django_windows_camera.get_windows_camera_status, name='get_windows_camera_status'),
]
'''
    
    # Crear archivos
    files_to_create = [
        (f"{base_dir}/camera_usb_detector.py", detector_content),
        (f"{base_dir}/windows_ptp_controller.py", controller_content),
        (f"{base_dir}/django_windows_camera.py", django_content),
        (f"{base_dir}/windows_camera_urls.py", urls_content),
    ]
    
    all_created = True
    for filepath, content in files_to_create:
        if not create_file_with_content(filepath, content):
            all_created = False
    
    if all_created:
        print(f"\n🎉 ¡Todos los archivos creados exitosamente!")
        print(f"\nPróximos pasos:")
        print(f"1. Ejecutar: python manage.py makemigrations")
        print(f"2. Ejecutar: python manage.py migrate")
        print(f"3. Expandir funcionalidad de los archivos según necesidades")
    else:
        print(f"\n⚠️ Algunos archivos no se pudieron crear")
    
    return all_created

if __name__ == "__main__":
    create_camera_files()