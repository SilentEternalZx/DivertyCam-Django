# django_usb_camera.py
# Integración de cámaras USB con Django

import json
import logging
import os
import time
import uuid
from typing import Dict, List, Optional
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.shortcuts import get_object_or_404
import threading
import base64
from io import BytesIO
from PIL import Image

# Importar nuestros controladores
from .camera_usb_detector import USBCameraDetector
from .ptp_controller import BasePTPController, PTPDeviceProperty
from .models import PhotoboothConfig, Evento

logger = logging.getLogger(__name__)

class DjangoUSBCameraManager:
    """
    Administrador de cámaras USB para Django
    """
    
    def __init__(self):
        self.detector = USBCameraDetector()
        self.active_controllers = {}  # session_id -> controller
        self.monitoring_thread = None
        self.is_monitoring = False
        
    def start_monitoring(self):
        """Inicia el monitoreo de cámaras en segundo plano"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitor_cameras,
                daemon=True
            )
            self.monitoring_thread.start()
            logger.info("Monitoreo de cámaras USB iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo de cámaras"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Monitoreo de cámaras USB detenido")
    
    def _monitor_cameras(self):
        """Función de monitoreo ejecutada en hilo separado"""
        def camera_callback(event_type, camera_info):
            logger.info(f"Evento de cámara: {event_type} - {camera_info.get('model', 'Unknown')}")
            # Aquí se pueden enviar notificaciones WebSocket si es necesario
        
        self.detector.monitor_camera_connections(
            callback=camera_callback,
            interval=3
        )
    
    def get_available_cameras(self) -> List[Dict]:
        """Obtiene lista de cámaras disponibles"""
        return self.detector.scan_for_cameras()
    
    def connect_camera(self, camera_info: Dict, session_id: str = None) -> Dict:
        """Conecta con una cámara específica"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        try:
            # Crear controlador PTP
            controller = BasePTPController(camera_info['device_object'])
            
            if controller.connect():
                self.active_controllers[session_id] = {
                    'controller': controller,
                    'camera_info': camera_info,
                    'connected_at': time.time()
                }
                
                return {
                    'success': True,
                    'session_id': session_id,
                    'camera_info': camera_info,
                    'device_info': controller.device_info
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo establecer conexión PTP'
                }
                
        except Exception as e:
            logger.error(f"Error conectando cámara: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def disconnect_camera(self, session_id: str) -> bool:
        """Desconecta una cámara"""
        if session_id in self.active_controllers:
            try:
                controller_info = self.active_controllers[session_id]
                controller_info['controller'].disconnect()
                del self.active_controllers[session_id]
                return True
            except Exception as e:
                logger.error(f"Error desconectando cámara: {str(e)}")
        return False
    
    def capture_image(self, session_id: str) -> Dict:
        """Captura una imagen con la cámara conectada"""
        if session_id not in self.active_controllers:
            return {
                'success': False,
                'error': 'Cámara no conectada'
            }
        
        try:
            controller_info = self.active_controllers[session_id]
            controller = controller_info['controller']
            
            # Capturar imagen
            if controller.capture_image():
                # En una implementación real, aquí deberíamos:
                # 1. Esperar a que la imagen esté disponible
                # 2. Descargar la imagen de la cámara
                # 3. Guardarla en el sistema de archivos
                
                # Por ahora, simulamos una captura exitosa
                return {
                    'success': True,
                    'message': 'Imagen capturada exitosamente',
                    'timestamp': time.time()
                }
            else:
                return {
                    'success': False,
                    'error': 'Error en comando de captura'
                }
                
        except Exception as e:
            logger.error(f"Error capturando imagen: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_camera_property(self, session_id: str, property_code: int, value) -> Dict:
        """Establece una propiedad de la cámara"""
        if session_id not in self.active_controllers:
            return {
                'success': False,
                'error': 'Cámara no conectada'
            }
        
        try:
            controller_info = self.active_controllers[session_id]
            controller = controller_info['controller']
            
            if controller.set_property_value(property_code, value):
                return {
                    'success': True,
                    'message': f'Propiedad {property_code} establecida'
                }
            else:
                return {
                    'success': False,
                    'error': 'Error estableciendo propiedad'
                }
                
        except Exception as e:
            logger.error(f"Error estableciendo propiedad: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_camera_property(self, session_id: str, property_code: int) -> Dict:
        """Obtiene el valor de una propiedad de la cámara"""
        if session_id not in self.active_controllers:
            return {
                'success': False,
                'error': 'Cámara no conectada'
            }
        
        try:
            controller_info = self.active_controllers[session_id]
            controller = controller_info['controller']
            
            value = controller.get_property_value(property_code)
            if value is not None:
                return {
                    'success': True,
                    'property_code': property_code,
                    'value': value
                }
            else:
                return {
                    'success': False,
                    'error': 'Error obteniendo propiedad'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo propiedad: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Instancia global del manager
usb_camera_manager = DjangoUSBCameraManager()

# ==================== VISTAS DJANGO ====================

@csrf_exempt
@require_GET
def detect_usb_cameras(request):
    """API para detectar cámaras USB conectadas"""
    try:
        cameras = usb_camera_manager.get_available_cameras()
        
        # Filtrar información sensible y preparar respuesta
        camera_list = []
        for camera in cameras:
            camera_data = {
                'id': f"{camera['vendor_id']:04x}:{camera['product_id']:04x}",
                'vendor_name': camera['vendor_name'],
                'product_name': camera['product_name'],
                'model': camera['model'],
                'serial_number': camera.get('serial_number'),
                'connection_type': camera['connection_type'],
                'is_available': camera['is_available']
            }
            camera_list.append(camera_data)
        
        return JsonResponse({
            'success': True,
            'cameras': camera_list,
            'count': len(camera_list)
        })
        
    except Exception as e:
        logger.error(f"Error detectando cámaras USB: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_POST
def connect_usb_camera(request):
    """API para conectar con una cámara USB específica"""
    try:
        data = json.loads(request.body)
        camera_id = data.get('camera_id')
        evento_id = data.get('evento_id')
        
        if not camera_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de cámara requerido'
            })
        
        # Buscar la cámara por ID
        cameras = usb_camera_manager.get_available_cameras()
        target_camera = None
        
        for camera in cameras:
            cam_id = f"{camera['vendor_id']:04x}:{camera['product_id']:04x}"
            if cam_id == camera_id:
                target_camera = camera
                break
        
        if not target_camera:
            return JsonResponse({
                'success': False,
                'error': 'Cámara no encontrada'
            })
        
        # Conectar cámara
        result = usb_camera_manager.connect_camera(target_camera)
        
        if result['success']:
            # Guardar información en la configuración si se proporciona evento_id
            if evento_id:
                try:
                    config = PhotoboothConfig.objects.get(evento_id=evento_id)
                    config.camera_id = result['session_id']
                    config.tipo_camara = 'usb_ptp'
                    config.save()
                except PhotoboothConfig.DoesNotExist:
                    pass
            
            return JsonResponse(result)
        else:
            return JsonResponse(result)
            
    except Exception as e:
        logger.error(f"Error conectando cámara USB: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_POST
def disconnect_usb_camera(request):
    """API para desconectar cámara USB"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID requerido'
            })
        
        success = usb_camera_manager.disconnect_camera(session_id)
        
        return JsonResponse({
            'success': success,
            'message': 'Cámara desconectada' if success else 'Error desconectando cámara'
        })
        
    except Exception as e:
        logger.error(f"Error desconectando cámara: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_POST
def capture_usb_photo(request):
    """API para capturar foto con cámara USB"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID requerido'
            })
        
        result = usb_camera_manager.capture_image(session_id)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error capturando foto USB: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_POST
def set_usb_camera_setting(request):
    """API para configurar parámetros de cámara USB"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        setting_name = data.get('setting_name')
        setting_value = data.get('setting_value')
        
        if not all([session_id, setting_name, setting_value is not None]):
            return JsonResponse({
                'success': False,
                'error': 'Datos incompletos'
            })
        
        # Mapear nombres de configuración a códigos PTP
        setting_map = {
            'iso': PTPDeviceProperty.EXPOSURE_INDEX,
            'aperture': PTPDeviceProperty.F_NUMBER,
            'shutter_speed': PTPDeviceProperty.EXPOSURE_TIME,
            'white_balance': PTPDeviceProperty.WHITE_BALANCE,
            'focus_mode': PTPDeviceProperty.FOCUS_MODE,
            'exposure_mode': PTPDeviceProperty.EXPOSURE_PROGRAM_MODE,
        }
        
        property_code = setting_map.get(setting_name)
        if not property_code:
            return JsonResponse({
                'success': False,
                'error': f'Configuración no soportada: {setting_name}'
            })
        
        result = usb_camera_manager.set_camera_property(
            session_id, 
            property_code, 
            setting_value
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error configurando cámara USB: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_GET
def get_usb_camera_setting(request):
    """API para obtener configuración actual de cámara USB"""
    try:
        session_id = request.GET.get('session_id')
        setting_name = request.GET.get('setting_name')
        
        if not all([session_id, setting_name]):
            return JsonResponse({
                'success': False,
                'error': 'Parámetros requeridos: session_id, setting_name'
            })
        
        # Mapear nombres de configuración a códigos PTP
        setting_map = {
            'iso': PTPDeviceProperty.EXPOSURE_INDEX,
            'aperture': PTPDeviceProperty.F_NUMBER,
            'shutter_speed': PTPDeviceProperty.EXPOSURE_TIME,
            'white_balance': PTPDeviceProperty.WHITE_BALANCE,
            'focus_mode': PTPDeviceProperty.FOCUS_MODE,
            'exposure_mode': PTPDeviceProperty.EXPOSURE_PROGRAM_MODE,
            'battery_level': PTPDeviceProperty.BATTERY_LEVEL,
        }
        
        property_code = setting_map.get(setting_name)
        if not property_code:
            return JsonResponse({
                'success': False,
                'error': f'Configuración no soportada: {setting_name}'
            })
        
        result = usb_camera_manager.get_camera_property(session_id, property_code)
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración USB: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_GET
def get_camera_status(request):
    """API para obtener estado de cámaras conectadas"""
    try:
        active_sessions = []
        
        for session_id, controller_info in usb_camera_manager.active_controllers.items():
            camera_info = controller_info['camera_info']
            connected_at = controller_info['connected_at']
            
            session_data = {
                'session_id': session_id,
                'camera_model': camera_info['model'],
                'vendor_name': camera_info['vendor_name'],
                'connected_at': connected_at,
                'connection_duration': time.time() - connected_at,
                'is_active': True
            }
            active_sessions.append(session_data)
        
        return JsonResponse({
            'success': True,
            'active_sessions': active_sessions,
            'total_connected': len(active_sessions)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de cámaras: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# ==================== FUNCIONES DE INICIALIZACIÓN ====================

def init_usb_camera_system():
    """Inicializa el sistema de cámaras USB"""
    try:
        usb_camera_manager.start_monitoring()
        logger.info("Sistema de cámaras USB inicializado")
        return True
    except Exception as e:
        logger.error(f"Error inicializando sistema USB: {str(e)}")
        return False

def shutdown_usb_camera_system():
    """Cierra el sistema de cámaras USB"""
    try:
        # Desconectar todas las cámaras activas
        for session_id in list(usb_camera_manager.active_controllers.keys()):
            usb_camera_manager.disconnect_camera(session_id)
        
        usb_camera_manager.stop_monitoring()
        logger.info("Sistema de cámaras USB cerrado")
        return True
    except Exception as e:
        logger.error(f"Error cerrando sistema USB: {str(e)}")
        return False

# ==================== SIGNAL HANDLERS ====================

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

@receiver(post_save, sender=PhotoboothConfig)
def handle_photobooth_config_save(sender, instance, created, **kwargs):
    """Maneja cambios en la configuración del photobooth"""
    if instance.tipo_camara == 'usb_ptp' and instance.camera_id:
        # Aplicar configuraciones específicas si hay una cámara conectada
        logger.info(f"Configuración USB actualizada para evento {instance.evento.id}")

# ==================== MIDDLEWARE (Opcional) ====================

class USBCameraMiddleware:
    """Middleware para gestión de cámaras USB"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Inicializar sistema al cargar Django
        init_usb_camera_system()
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def __del__(self):
        # Limpiar al cerrar Django
        shutdown_usb_camera_system()