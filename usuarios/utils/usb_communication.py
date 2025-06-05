# usuarios/utils/usb_communication.py
import os
import subprocess
import json
import shutil
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class USBCommunication:
    def __init__(self):
        # Obtener ruta de ADB desde settings o usar default
        self.adb_path = getattr(settings, 'ADB_PATH', 'adb')
        
        # Carpeta en el dispositivo Android
        self.device_folder = '/sdcard/photobooth/'
        
        # Carpeta temporal en Windows
        self.temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp_usb')
        
        # Crear carpeta temporal si no existe
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def check_device_connected(self):
        """Verifica si hay un dispositivo Android conectado"""
        try:
            result = subprocess.run([self.adb_path, 'devices'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"Error ejecutando ADB: {result.stderr}")
                return False, []
            
            lines = result.stdout.strip().split('\n')[1:]  # Omitir header
            connected_devices = [line for line in lines if '\tdevice' in line]
            
            return len(connected_devices) > 0, connected_devices
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout verificando dispositivos ADB")
            return False, []
        except FileNotFoundError:
            logger.error(f"ADB no encontrado en la ruta: {self.adb_path}")
            return False, []
        except Exception as e:
            logger.error(f"Error verificando dispositivos: {e}")
            return False, []
    
    def setup_device_folder(self):
        """Crea la carpeta del photobooth en el dispositivo Android"""
        try:
            # Crear carpeta principal
            result1 = subprocess.run([self.adb_path, 'shell', 'mkdir', '-p', self.device_folder], 
                          capture_output=True, timeout=10)
            
            # Crear subcarpetas
            subprocess.run([self.adb_path, 'shell', 'mkdir', '-p', f'{self.device_folder}images'], 
                          capture_output=True, timeout=10)
            subprocess.run([self.adb_path, 'shell', 'mkdir', '-p', f'{self.device_folder}data'], 
                          capture_output=True, timeout=10)
            subprocess.run([self.adb_path, 'shell', 'mkdir', '-p', f'{self.device_folder}responses'], 
                          capture_output=True, timeout=10)
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout configurando carpetas en dispositivo")
            return False
        except Exception as e:
            logger.error(f"Error configurando carpetas: {e}")
            return False
    
    def send_collage_to_device(self, collage_path, session_id, metadata=None):
        """Envía el collage al dispositivo móvil"""
        try:
            # Verificar que el dispositivo esté conectado
            is_connected, devices = self.check_device_connected()
            if not is_connected:
                return False, "No hay dispositivo Android conectado por USB"
            
            # Verificar que el archivo existe
            if not os.path.exists(collage_path):
                return False, f"Archivo de collage no encontrado: {collage_path}"
            
            # Configurar carpetas en el dispositivo
            if not self.setup_device_folder():
                return False, "Error configurando carpetas en el dispositivo"
            
            # Nombre del archivo en el dispositivo
            filename = f"collage_{session_id}.jpg"
            device_image_path = f"{self.device_folder}images/{filename}"
            
            logger.info(f"Enviando {collage_path} a {device_image_path}")
            
            # Copiar imagen al dispositivo
            copy_result = subprocess.run([
                self.adb_path, 'push', 
                collage_path, 
                device_image_path
            ], capture_output=True, text=True, timeout=30)
            
            if copy_result.returncode != 0:
                logger.error(f"Error copiando imagen: {copy_result.stderr}")
                return False, f"Error copiando imagen: {copy_result.stderr}"
            
            # Crear archivo de metadatos
            metadata_info = {
                'session_id': session_id,
                'filename': filename,
                'timestamp': timezone.now().isoformat(),
                'status': 'pending',
                'metadata': metadata or {}
            }
            
            # Guardar metadatos localmente y enviar al dispositivo
            metadata_file = os.path.join(self.temp_folder, f"metadata_{session_id}.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_info, f, ensure_ascii=False, indent=2)
            
            device_metadata_path = f"{self.device_folder}data/metadata_{session_id}.json"
            metadata_result = subprocess.run([
                self.adb_path, 'push', 
                metadata_file, 
                device_metadata_path
            ], capture_output=True, text=True, timeout=10)
            
            if metadata_result.returncode != 0:
                logger.warning(f"Error enviando metadatos: {metadata_result.stderr}")
            
            # Crear archivo de señal para la app Android
            signal_file = os.path.join(self.temp_folder, f"signal_{session_id}.txt")
            with open(signal_file, 'w') as f:
                f.write(f"NEW_COLLAGE:{session_id}:{filename}")
            
            device_signal_path = f"{self.device_folder}signal_{session_id}.txt"
            signal_result = subprocess.run([
                self.adb_path, 'push', 
                signal_file, 
                device_signal_path
            ], capture_output=True, text=True, timeout=10)
            
            # Limpiar archivos temporales
            try:
                os.remove(metadata_file)
                os.remove(signal_file)
            except:
                pass
            
            if signal_result.returncode != 0:
                logger.warning(f"Error enviando señal: {signal_result.stderr}")
                # Aún así retornamos éxito porque la imagen se copió
            
            logger.info(f"Collage enviado exitosamente a dispositivo móvil")
            return True, "Collage enviado exitosamente al dispositivo móvil"
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout en comunicación USB")
            return False, "Timeout en comunicación USB"
        except Exception as e:
            logger.error(f"Error enviando collage: {e}")
            return False, f"Error inesperado: {str(e)}"
    
    def check_transfer_status(self, session_id):
        """Verifica el estado de la transferencia"""
        try:
            # Verificar si existe el archivo de respuesta
            response_path = f"{self.device_folder}responses/response_{session_id}.json"
            
            # Obtener el archivo del dispositivo
            temp_response = os.path.join(self.temp_folder, f"response_{session_id}.json")
            
            pull_result = subprocess.run([
                self.adb_path, 'pull', 
                response_path, 
                temp_response
            ], capture_output=True, text=True, timeout=10)
            
            if pull_result.returncode == 0 and os.path.exists(temp_response):
                with open(temp_response, 'r', encoding='utf-8') as f:
                    response_data = json.load(f)
                
                # Limpiar archivo temporal
                try:
                    os.remove(temp_response)
                except:
                    pass
                
                return True, response_data
            else:
                # No hay respuesta disponible aún
                return False, "Respuesta no disponible"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout verificando estado"
        except Exception as e:
            logger.error(f"Error verificando estado: {e}")
            return False, f"Error: {str(e)}"
    
    def get_device_info(self):
        """Obtiene información del dispositivo conectado"""
        try:
            is_connected, devices = self.check_device_connected()
            if not is_connected:
                return None
            
            # Obtener información del dispositivo
            commands = {
                'model': ['shell', 'getprop', 'ro.product.model'],
                'manufacturer': ['shell', 'getprop', 'ro.product.manufacturer'],
                'android_version': ['shell', 'getprop', 'ro.build.version.release']
            }
            
            device_info = {'devices': devices}
            
            for key, command in commands.items():
                try:
                    result = subprocess.run([self.adb_path] + command, 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        device_info[key] = result.stdout.strip()
                    else:
                        device_info[key] = 'Unknown'
                except:
                    device_info[key] = 'Unknown'
            
            return device_info
            
        except Exception as e:
            logger.error(f"Error obteniendo info del dispositivo: {e}")
            return None
    
    def test_connection(self):
        """Prueba la conexión con el dispositivo"""
        try:
            is_connected, devices = self.check_device_connected()
            if not is_connected:
                return False, "No hay dispositivos conectados"
            
            # Probar comando simple
            test_result = subprocess.run([
                self.adb_path, 'shell', 'echo', 'test'
            ], capture_output=True, text=True, timeout=5)
            
            if test_result.returncode == 0 and 'test' in test_result.stdout:
                return True, f"Conexión exitosa con {len(devices)} dispositivo(s)"
            else:
                return False, "Dispositivo conectado pero no responde"
                
        except Exception as e:
            return False, f"Error en prueba de conexión: {str(e)}"