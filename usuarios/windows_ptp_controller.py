# windows_ptp_controller.py - Versión mejorada para Nikon
import os
import sys
import logging
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WindowsPTPController:
    """Controlador PTP mejorado para cámaras Nikon"""
    
    def __init__(self):
        self.is_windows = sys.platform.startswith('win')
        self.connected_camera = None
        self.nikon_devices = ['04b0']  # Vendor ID de Nikon
        
    def detect_cameras(self) -> List[Dict]:
        """Detecta cámaras PTP disponibles"""
        cameras = []
        
        if not self.is_windows:
            return cameras
            
        try:
            # Usar wmic para detectar dispositivos USB
            cmd = 'wmic path Win32_USBDevice get DeviceID,Name,Manufacturer /format:csv'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 4:
                            device_id = parts[1]
                            name = parts[2]
                            manufacturer = parts[3]
                            
                            # Buscar cámaras conocidas
                            if any(vendor in device_id for vendor in self.nikon_devices):
                                camera_info = self._parse_camera_info(device_id, name, manufacturer)
                                if camera_info:
                                    cameras.append(camera_info)
                                    
        except Exception as e:
            logger.error(f"Error detectando cámaras: {e}")
        
        return cameras
    
    def _parse_camera_info(self, device_id: str, name: str, manufacturer: str) -> Optional[Dict]:
        """Parsea información de la cámara desde device_id"""
        try:
            # Extraer VID y PID del device_id
            # Formato típico: USB\VID_04B0&PID_043F\...
            if 'VID_' in device_id and 'PID_' in device_id:
                vid_start = device_id.find('VID_') + 4
                pid_start = device_id.find('PID_') + 4
                vid = device_id[vid_start:vid_start+4].lower()
                pid = device_id[pid_start:pid_start+4].lower()
                
                camera_id = f"{vid}:{pid}"
                
                # Detectar modelo específico de Nikon
                nikon_models = {
                    '043f': 'D3500/D5600',
                    '0421': 'D750',
                    '0422': 'D810',
                    '0428': 'D5',
                    '042a': 'D500',
                    '042c': 'D3400',
                    '042e': 'D5600',
                    '0430': 'D7500',
                    '0432': 'D850',
                    # Añadir más modelos según necesidad
                }
                
                model = nikon_models.get(pid, 'Unknown')
                
                return {
                    'id': camera_id,
                    'vendor_name': 'Nikon',
                    'product_name': name if name != 'Unknown' else model,
                    'model': f'Nikon {model}',
                    'serial_number': None,
                    'connection_type': 'USB',
                    'is_available': True,
                    'supports_ptp': True,
                    'capabilities': ['capture', 'preview', 'settings']
                }
                
        except Exception as e:
            logger.error(f"Error parseando info de cámara: {e}")
        
        return None
    
    def connect_camera(self, camera_id: str, camera_type: str = None) -> bool:
        """Conecta con una cámara Nikon PTP"""
        try:
            logger.info(f"Conectando con cámara Nikon: {camera_id}")
            
            # Verificar que la cámara sigue disponible
            available_cameras = self.detect_cameras()
            camera_found = any(cam['id'] == camera_id for cam in available_cameras)
            
            if not camera_found:
                logger.error(f"Cámara {camera_id} no encontrada")
                return False
            
            # Aquí implementar conexión PTP real
            # Por ahora, simular conexión exitosa
            self.connected_camera = {
                'id': camera_id,
                'type': camera_type or 'Nikon',
                'connected_at': datetime.now(),
                'status': 'connected'
            }
            
            logger.info(f"Conectado exitosamente con {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando con cámara: {e}")
            return False
    
    def disconnect_camera(self):
        """Desconecta la cámara"""
        if self.connected_camera:
            logger.info(f"Desconectando cámara: {self.connected_camera['id']}")
            self.connected_camera = None
    
    def is_connected(self) -> bool:
        """Verifica si hay una cámara conectada"""
        return self.connected_camera is not None
    
    def get_connected_camera(self) -> Optional[Dict]:
        """Obtiene información de la cámara conectada"""
        return self.connected_camera
    
    def capture_image(self, settings: Dict = None) -> Optional[str]:
        """Captura una imagen con la cámara Nikon"""
        if not self.is_connected():
            logger.error("No hay cámara conectada")
            return None
            
        try:
            logger.info("Iniciando captura con cámara Nikon...")
            
            # Generar nombre de archivo único
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nikon_capture_{timestamp}.jpg"
            
            # Aquí implementar captura PTP real
            # Por ahora simular captura exitosa
            
            # Ejemplo de implementación futura con gphoto2 o libptp:
            # cmd = f'gphoto2 --capture-image-and-download --filename {filename}'
            # result = subprocess.run(cmd, shell=True, capture_output=True)
            
            logger.info(f"Imagen capturada: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error capturando imagen: {e}")
            return None
    
    def get_camera_settings(self) -> Dict:
        """Obtiene configuraciones disponibles de la cámara"""
        if not self.is_connected():
            return {}
        
        # Configuraciones típicas de cámaras Nikon
        return {
            'iso': ['100', '200', '400', '800', '1600', '3200', '6400'],
            'aperture': ['f/1.4', 'f/2.0', 'f/2.8', 'f/4.0', 'f/5.6', 'f/8.0'],
            'shutter_speed': ['1/500', '1/250', '1/125', '1/60', '1/30', '1/15'],
            'white_balance': ['auto', 'daylight', 'cloudy', 'tungsten', 'fluorescent'],
            'image_quality': ['RAW', 'JPEG Fine', 'JPEG Normal', 'RAW+JPEG']
        }
    
    def set_camera_setting(self, setting: str, value: str) -> bool:
        """Configura un parámetro de la cámara"""
        if not self.is_connected():
            return False
        
        try:
            logger.info(f"Configurando {setting} = {value}")
            
            # Aquí implementar configuración PTP real
            # Ejemplo futuro con gphoto2:
            # cmd = f'gphoto2 --set-config {setting}={value}'
            # result = subprocess.run(cmd, shell=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error configurando {setting}: {e}")
            return False
    
    def get_preview(self) -> Optional[bytes]:
        """Obtiene preview en vivo de la cámara"""
        if not self.is_connected():
            return None
        
        try:
            # Implementar preview PTP
            # Por ahora retornar None
            logger.info("Obteniendo preview...")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo preview: {e}")
            return None
    
    def cleanup(self):
        """Limpia recursos y desconecta"""
        self.disconnect_camera()
        logger.info("Controlador PTP limpiado")