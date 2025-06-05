# archivo: nikon_qdslrdashboard.py

import requests
import json
import time
import os
import shutil
import logging
from datetime import datetime
import subprocess
import platform

logger = logging.getLogger(__name__)

class NikonQDslrDashboard:
    """
    Controlador universal para cualquier cámara Nikon compatible
    usando qDslrDashboard Server
    """
    
    def __init__(self, server_port=4757):
        self.server_url = f"http://localhost:{server_port}"
        self.server_port = server_port
        self.connected = False
        self.camera_info = None
        self.camera_id = None
        self.server_process = None
        
    def start_server(self):
        """Iniciar qDslrDashboard Server automáticamente"""
        try:
            # Verificar si el servidor ya está corriendo
            if self.check_server_status():
                logger.info("qDslrDashboard Server ya está corriendo")
                return True
            
            # Rutas posibles del ejecutable
            possible_paths = [
                r"C:\Program Files\qDslrDashboard\qDslrDashboardServer.exe",
                r"C:\Program Files (x86)\qDslrDashboard\qDslrDashboardServer.exe",
                os.path.join(os.environ.get('PROGRAMFILES', ''), 'qDslrDashboard', 'qDslrDashboardServer.exe'),
                os.path.join(os.path.dirname(__file__), 'tools', 'qDslrDashboardServer.exe'),
            ]
            
            server_exe = None
            for path in possible_paths:
                if os.path.exists(path):
                    server_exe = path
                    break
            
            if not server_exe:
                logger.error("No se encontró qDslrDashboardServer.exe")
                return False
            
            # Iniciar el servidor
            if platform.system() == 'Windows':
                self.server_process = subprocess.Popen(
                    [server_exe, '--port', str(self.server_port)],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.server_process = subprocess.Popen(
                    [server_exe, '--port', str(self.server_port)]
                )
            
            # Esperar a que el servidor inicie
            time.sleep(3)
            
            # Verificar que esté corriendo
            return self.check_server_status()
            
        except Exception as e:
            logger.error(f"Error iniciando servidor: {e}")
            return False
    
    def check_server_status(self):
        """Verificar si el servidor está activo"""
        try:
            response = requests.get(f"{self.server_url}/server/version", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def detect_cameras(self):
        """Detectar todas las cámaras Nikon conectadas"""
        try:
            response = requests.get(f"{self.server_url}/cameras", timeout=5)
            
            if response.status_code == 200:
                cameras = response.json()
                nikon_cameras = []
                
                for camera in cameras:
                    # Filtrar solo cámaras Nikon
                    if 'nikon' in camera.get('vendor', '').lower():
                        nikon_cameras.append({
                            'id': camera['id'],
                            'model': camera.get('model', 'Unknown'),
                            'serial': camera.get('serial', ''),
                            'battery': camera.get('battery_level', 0),
                            'status': camera.get('status', 'ready')
                        })
                
                logger.info(f"Cámaras Nikon detectadas: {len(nikon_cameras)}")
                return nikon_cameras
            
            return []
            
        except Exception as e:
            logger.error(f"Error detectando cámaras: {e}")
            return []
    
    def connect(self, camera_id=None):
        """
        Conectar con una cámara Nikon
        Si no se especifica camera_id, conecta con la primera disponible
        """
        try:
            # Asegurar que el servidor esté corriendo
            if not self.check_server_status():
                if not self.start_server():
                    return False
            
            # Detectar cámaras disponibles
            cameras = self.detect_cameras()
            
            if not cameras:
                logger.error("No se detectaron cámaras Nikon")
                return False
            
            # Seleccionar cámara
            if camera_id:
                camera = next((c for c in cameras if c['id'] == camera_id), None)
                if not camera:
                    logger.error(f"No se encontró cámara con ID: {camera_id}")
                    return False
            else:
                # Usar la primera cámara disponible
                camera = cameras[0]
            
            # Conectar con la cámara
            response = requests.post(
                f"{self.server_url}/camera/{camera['id']}/connect",
                timeout=10
            )
            
            if response.status_code == 200:
                self.connected = True
                self.camera_id = camera['id']
                self.camera_info = camera
                logger.info(f"Conectado a: {camera['model']} (ID: {camera['id']})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            return False
    
    def disconnect(self):
        """Desconectar de la cámara"""
        try:
            if self.connected and self.camera_id:
                requests.post(f"{self.server_url}/camera/{self.camera_id}/disconnect")
                self.connected = False
                self.camera_id = None
                logger.info("Desconectado de la cámara")
        except:
            pass
    
    def get_camera_settings(self):
        """Obtener configuraciones actuales de la cámara"""
        if not self.connected:
            return None
        
        try:
            response = requests.get(
                f"{self.server_url}/camera/{self.camera_id}/settings"
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo configuraciones: {e}")
            return None
    
    def set_camera_setting(self, setting_name, value):
        """Configurar un parámetro individual de la cámara"""
        if not self.connected:
            return False
        
        try:
            data = {setting_name: value}
            response = requests.put(
                f"{self.server_url}/camera/{self.camera_id}/settings",
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"{setting_name} = {value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error configurando {setting_name}: {e}")
            return False
    
    def set_multiple_settings(self, settings_dict):
        """Configurar múltiples parámetros a la vez"""
        if not self.connected:
            return False
        
        try:
            response = requests.put(
                f"{self.server_url}/camera/{self.camera_id}/settings",
                json=settings_dict
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error configurando múltiples ajustes: {e}")
            return False
    
    def capture_photo(self, download_path=None, use_af=True):
        """
        Capturar foto usando el OBTURADOR FÍSICO de la cámara
        
        Args:
            download_path: Ruta donde guardar la foto
            use_af: Si True, enfoca antes de capturar
        
        Returns:
            Ruta del archivo guardado o None si falla
        """
        if not self.connected:
            logger.error("No hay cámara conectada")
            return None
        
        try:
            # Enfocar si está habilitado
            if use_af:
                af_response = requests.post(
                    f"{self.server_url}/camera/{self.camera_id}/autofocus"
                )
                if af_response.status_code == 200:
                    time.sleep(0.5)  # Esperar a que enfoque
            
            # Capturar foto
            capture_response = requests.post(
                f"{self.server_url}/camera/{self.camera_id}/capture",
                json={"download": True}
            )
            
            if capture_response.status_code != 200:
                logger.error("Error al capturar foto")
                return None
            
            capture_data = capture_response.json()
            
            # Esperar a que la cámara procese
            time.sleep(1)
            
            # Descargar la imagen
            if 'image_url' in capture_data:
                image_url = capture_data['image_url']
                
                # Si la URL no es completa, construirla
                if not image_url.startswith('http'):
                    image_url = f"{self.server_url}{image_url}"
                
                # Descargar imagen
                img_response = requests.get(image_url, stream=True)
                
                if img_response.status_code == 200:
                    # Determinar nombre de archivo
                    if not download_path:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        model_name = self.camera_info['model'].replace(' ', '_')
                        filename = f"NIKON_{model_name}_{timestamp}.jpg"
                        download_path = os.path.join(os.getcwd(), 'captures', filename)
                    
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(download_path), exist_ok=True)
                    
                    # Guardar imagen
                    with open(download_path, 'wb') as f:
                        shutil.copyfileobj(img_response.raw, f)
                    
                    logger.info(f"Foto guardada: {download_path}")
                    return download_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error capturando foto: {e}")
            return None
    
    def start_liveview(self):
        """Iniciar LiveView"""
        if not self.connected:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/camera/{self.camera_id}/liveview/start"
            )
            return response.status_code == 200
        except:
            return False
    
    def stop_liveview(self):
        """Detener LiveView"""
        if not self.connected:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/camera/{self.camera_id}/liveview/stop"
            )
            return response.status_code == 200
        except:
            return False
    
    def get_liveview_image(self):
        """Obtener imagen actual del LiveView"""
        if not self.connected:
            return None
        
        try:
            response = requests.get(
                f"{self.server_url}/camera/{self.camera_id}/liveview/image",
                stream=True
            )
            
            if response.status_code == 200:
                return response.content
            
            return None
        except:
            return None
    
    def stop_server(self):
        """Detener el servidor qDslrDashboard"""
        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
                logger.info("Servidor qDslrDashboard detenido")
        except:
            pass