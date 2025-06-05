# camera_usb_detector.py
import usb.core
import usb.util
import logging
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)

class USBCameraDetector:
    """
    Detector base para cámaras USB usando PyUSB
    """
    
    # Vendor IDs de fabricantes de cámaras conocidos
    CAMERA_VENDORS = {
        0x04b0: 'Nikon',
        0x04a9: 'Canon', 
        0x054c: 'Sony',
        0x03f0: 'HP',
        0x04da: 'Panasonic',
        0x040a: 'Kodak',
        0x04e8: 'Samsung',
        0x05ac: 'Apple',
        0x04cc: 'Fujifilm',
        0x0547: 'Anchor Chips',
    }
    
    # Product IDs específicos de cámaras Nikon (ejemplos)
    NIKON_CAMERAS = {
        0x0402: 'D100',
        0x0403: 'D2H',
        0x0404: 'D70',
        0x0405: 'D70s',
        0x0406: 'D2X',
        0x0407: 'D50',
        0x0408: 'D2Xs',
        0x0409: 'D40',
        0x040a: 'D40x',
        0x040c: 'D80',
        0x040d: 'D200',
        0x040e: 'D300',
        0x040f: 'D3',
        0x0410: 'D60',
        0x0411: 'D90',
        0x0412: 'D700',
        0x0413: 'D5000',
        0x0414: 'D3000',
        0x0415: 'D300s',
        0x0416: 'D3s',
        0x0417: 'D7000',
        0x0418: 'D5100',
        0x0419: 'D800/D800E',
        0x041a: 'D4',
        0x041b: 'D600',
        0x041c: 'D7100',
        0x041d: 'D5200',
        0x041e: 'D610',
        0x041f: 'D750',
        0x0420: 'D810',
        0x0421: 'D7200',
        0x0422: 'D5300',
        0x0423: 'D3300',
        0x0424: 'D5500',
        0x0425: 'D7500',
        0x0426: 'D850',
        0x0427: 'D780',
        0x0428: 'Z6',
        0x0429: 'Z7',
        0x042a: 'Z5',
        0x042b: 'Z6II',
        0x042c: 'Z7II',
        0x042d: 'Z9',
        0x042e: 'Z fc',
        0x042f: 'Z mc',
    }
    
    def __init__(self):
        self.detected_cameras = []
        
    def scan_for_cameras(self) -> List[Dict]:
        """
        Escanea puertos USB buscando cámaras conectadas
        """
        cameras = []
        
        try:
            # Buscar todos los dispositivos USB
            devices = usb.core.find(find_all=True)
            
            for device in devices:
                try:
                    # Verificar si es una cámara por vendor ID
                    if device.idVendor in self.CAMERA_VENDORS:
                        camera_info = self._get_camera_info(device)
                        if camera_info:
                            cameras.append(camera_info)
                            logger.info(f"Cámara detectada: {camera_info['model']}")
                        
                except Exception as e:
                    logger.debug(f"Error al verificar dispositivo USB: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error al escanear dispositivos USB: {str(e)}")
            
        self.detected_cameras = cameras
        return cameras
    
    def _get_camera_info(self, device) -> Optional[Dict]:
        """
        Extrae información de una cámara USB detectada
        """
        try:
            vendor_name = self.CAMERA_VENDORS.get(device.idVendor, 'Unknown')
            
            # Obtener nombre del producto si está disponible
            product_name = "Unknown"
            try:
                if device.product:
                    product_name = device.product
                elif device.idVendor == 0x04b0:  # Nikon
                    product_name = self.NIKON_CAMERAS.get(device.idProduct, f"Nikon Camera {hex(device.idProduct)}")
            except Exception:
                pass
            
            # Obtener número de serie si está disponible
            serial_number = None
            try:
                if device.serial_number:
                    serial_number = device.serial_number
            except Exception:
                pass
            
            camera_info = {
                'vendor_id': device.idVendor,
                'product_id': device.idProduct,
                'vendor_name': vendor_name,
                'product_name': product_name,
                'model': f"{vendor_name} {product_name}",
                'serial_number': serial_number,
                'bus': device.bus,
                'address': device.address,
                'device_object': device,
                'connection_type': 'USB',
                'is_available': True
            }
            
            return camera_info
            
        except Exception as e:
            logger.error(f"Error al obtener información de la cámara: {str(e)}")
            return None
    
    def get_camera_by_serial(self, serial_number: str) -> Optional[Dict]:
        """
        Busca una cámara específica por número de serie
        """
        for camera in self.detected_cameras:
            if camera.get('serial_number') == serial_number:
                return camera
        return None
    
    def get_cameras_by_vendor(self, vendor_name: str) -> List[Dict]:
        """
        Filtra cámaras por fabricante
        """
        return [cam for cam in self.detected_cameras 
                if cam.get('vendor_name', '').lower() == vendor_name.lower()]
    
    def is_camera_connected(self, vendor_id: int, product_id: int) -> bool:
        """
        Verifica si una cámara específica está conectada
        """
        try:
            device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
            return device is not None
        except Exception:
            return False
    
    def monitor_camera_connections(self, callback=None, interval=2):
        """
        Monitorea cambios en las conexiones de cámaras
        """
        previous_cameras = set()
        
        while True:
            try:
                current_cameras = self.scan_for_cameras()
                current_set = set((cam['vendor_id'], cam['product_id']) for cam in current_cameras)
                
                # Detectar nuevas conexiones
                new_cameras = current_set - previous_cameras
                if new_cameras and callback:
                    for vendor_id, product_id in new_cameras:
                        camera = next((cam for cam in current_cameras 
                                     if cam['vendor_id'] == vendor_id and cam['product_id'] == product_id), None)
                        if camera:
                            callback('connected', camera)
                
                # Detectar desconexiones
                disconnected_cameras = previous_cameras - current_set
                if disconnected_cameras and callback:
                    for vendor_id, product_id in disconnected_cameras:
                        callback('disconnected', {'vendor_id': vendor_id, 'product_id': product_id})
                
                previous_cameras = current_set
                time.sleep(interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error en monitoreo de cámaras: {str(e)}")
                time.sleep(interval)

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Crear detector
    detector = USBCameraDetector()
    
    # Escanear cámaras
    cameras = detector.scan_for_cameras()
    
    print(f"Se encontraron {len(cameras)} cámaras:")
    for camera in cameras:
        print(f"  - {camera['model']} (Serial: {camera.get('serial_number', 'N/A')})")
        print(f"    USB: {camera['vendor_id']:04x}:{camera['product_id']:04x}")
        print(f"    Bus: {camera['bus']}, Address: {camera['address']}")
        print()