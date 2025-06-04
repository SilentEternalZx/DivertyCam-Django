# django_windows_camera.py
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