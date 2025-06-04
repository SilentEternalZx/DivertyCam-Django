# ptp_controller.py
import usb.core
import usb.util
import struct
import time
import logging
from typing import Optional, Dict, List, Tuple, Any
from enum import IntEnum
import io
from PIL import Image

logger = logging.getLogger(__name__)

class PTPOpCode(IntEnum):
    """Códigos de operación PTP estándar"""
    # Operaciones básicas
    GET_DEVICE_INFO = 0x1001
    OPEN_SESSION = 0x1002
    CLOSE_SESSION = 0x1003
    GET_STORAGE_IDS = 0x1004
    GET_STORAGE_INFO = 0x1005
    GET_NUM_OBJECTS = 0x1006
    GET_OBJECT_HANDLES = 0x1007
    GET_OBJECT_INFO = 0x1008
    GET_OBJECT = 0x1009
    GET_THUMB = 0x100A
    DELETE_OBJECT = 0x100B
    SEND_OBJECT_INFO = 0x100C
    SEND_OBJECT = 0x100D
    INITIATE_CAPTURE = 0x100E
    FORMAT_STORE = 0x100F
    RESET_DEVICE = 0x1010
    SELF_TEST = 0x1011
    SET_OBJECT_PROTECTION = 0x1012
    POWER_DOWN = 0x1013
    GET_DEVICE_PROP_DESC = 0x1014
    GET_DEVICE_PROP_VALUE = 0x1015
    SET_DEVICE_PROP_VALUE = 0x1016
    RESET_DEVICE_PROP_VALUE = 0x1017
    TERMINATE_OPEN_CAPTURE = 0x1018
    MOVE_OBJECT = 0x1019
    COPY_OBJECT = 0x101A
    GET_PARTIAL_OBJECT = 0x101B
    INITIATE_OPEN_CAPTURE = 0x101C

class PTPResponseCode(IntEnum):
    """Códigos de respuesta PTP"""
    OK = 0x2001
    GENERAL_ERROR = 0x2002
    SESSION_NOT_OPEN = 0x2003
    INVALID_TRANSACTION_ID = 0x2004
    OPERATION_NOT_SUPPORTED = 0x2005
    PARAMETER_NOT_SUPPORTED = 0x2006
    INCOMPLETE_TRANSFER = 0x2007
    INVALID_STORAGE_ID = 0x2008
    INVALID_OBJECT_HANDLE = 0x2009
    DEVICE_PROP_NOT_SUPPORTED = 0x200A
    INVALID_OBJECT_FORMAT_CODE = 0x200B
    STORAGE_FULL = 0x200C
    OBJECT_WRITE_PROTECTED = 0x200D
    STORE_READ_ONLY = 0x200E
    ACCESS_DENIED = 0x200F
    NO_THUMBNAIL_PRESENT = 0x2010
    SELF_TEST_FAILED = 0x2011
    PARTIAL_DELETION = 0x2012
    STORE_NOT_AVAILABLE = 0x2013
    SPECIFICATION_BY_FORMAT_UNSUPPORTED = 0x2014
    NO_VALID_OBJECT_INFO = 0x2015
    INVALID_CODE_FORMAT = 0x2016
    UNKNOWN_VENDOR_CODE = 0x2017
    CAPTURE_ALREADY_TERMINATED = 0x2018
    DEVICE_BUSY = 0x2019
    INVALID_PARENT_OBJECT = 0x201A
    INVALID_DEVICE_PROP_FORMAT = 0x201B
    INVALID_DEVICE_PROP_VALUE = 0x201C
    INVALID_PARAMETER = 0x201D
    SESSION_ALREADY_OPEN = 0x201E
    TRANSACTION_CANCELLED = 0x201F
    SPECIFICATION_OF_DESTINATION_UNSUPPORTED = 0x2020

class PTPDeviceProperty(IntEnum):
    """Propiedades estándar de dispositivo PTP"""
    BATTERY_LEVEL = 0x5001
    FUNCTIONAL_MODE = 0x5002
    IMAGE_SIZE = 0x5003
    COMPRESSION_SETTING = 0x5004
    WHITE_BALANCE = 0x5005
    RGB_GAIN = 0x5006
    F_NUMBER = 0x5007
    FOCAL_LENGTH = 0x5008
    FOCUS_DISTANCE = 0x5009
    FOCUS_MODE = 0x500A
    EXPOSURE_METERING_MODE = 0x500B
    FLASH_MODE = 0x500C
    EXPOSURE_TIME = 0x500D
    EXPOSURE_PROGRAM_MODE = 0x500E
    EXPOSURE_INDEX = 0x500F
    EXPOSURE_BIAS_COMPENSATION = 0x5010
    DATE_TIME = 0x5011
    CAPTURE_DELAY = 0x5012
    STILL_CAPTURE_MODE = 0x5013
    CONTRAST = 0x5014
    SHARPNESS = 0x5015
    DIGITAL_ZOOM = 0x5016
    EFFECT_MODE = 0x5017
    BURST_NUMBER = 0x5018
    BURST_INTERVAL = 0x5019
    TIMELAPSE_NUMBER = 0x501A
    TIMELAPSE_INTERVAL = 0x501B
    FOCUS_METERING_MODE = 0x501C
    UPLOAD_URL = 0x501D
    ARTIST = 0x501E
    COPYRIGHT_INFO = 0x501F

class PTPContainer:
    """Contenedor para mensajes PTP"""
    
    CONTAINER_TYPE_COMMAND = 1
    CONTAINER_TYPE_DATA = 2
    CONTAINER_TYPE_RESPONSE = 3
    CONTAINER_TYPE_EVENT = 4
    
    def __init__(self, container_type: int, code: int, transaction_id: int, params: List[int] = None):
        self.container_type = container_type
        self.code = code
        self.transaction_id = transaction_id
        self.params = params or []
        self.data = b''
    
    def pack(self) -> bytes:
        """Empaqueta el contenedor en bytes para envío"""
        # Header: length(4) + type(2) + code(2) + transaction_id(4) = 12 bytes
        param_count = len(self.params)
        data_length = len(self.data)
        total_length = 12 + (param_count * 4) + data_length
        
        header = struct.pack('<IHHI', total_length, self.container_type, self.code, self.transaction_id)
        
        # Añadir parámetros
        params_data = b''
        for param in self.params:
            params_data += struct.pack('<I', param)
        
        return header + params_data + self.data
    
    @classmethod
    def unpack(cls, data: bytes) -> 'PTPContainer':
        """Desempaqueta bytes recibidos en un contenedor PTP"""
        if len(data) < 12:
            raise ValueError("Datos PTP insuficientes")
        
        length, container_type, code, transaction_id = struct.unpack('<IHHI', data[:12])
        
        container = cls(container_type, code, transaction_id)
        
        # Extraer parámetros (si los hay)
        pos = 12
        while pos < len(data) and (pos - 12) % 4 == 0:
            if pos + 4 <= len(data):
                param = struct.unpack('<I', data[pos:pos+4])[0]
                container.params.append(param)
                pos += 4
            else:
                break
        
        # El resto son datos
        if pos < len(data):
            container.data = data[pos:]
        
        return container

class BasePTPController:
    """Controlador base para comunicación PTP con cámaras"""
    
    def __init__(self, usb_device):
        self.device = usb_device
        self.interface_number = None
        self.endpoint_out = None
        self.endpoint_in = None
        self.endpoint_interrupt = None
        self.session_id = 1
        self.transaction_id = 0
        self.is_connected = False
        
        # Información del dispositivo
        self.device_info = {}
        
        # Configuración de timeout
        self.timeout = 5000  # 5 segundos
        
    def connect(self) -> bool:
        """Establece conexión con la cámara"""
        try:
            # Configurar dispositivo USB
            if self.device.is_kernel_driver_active(0):
                try:
                    self.device.detach_kernel_driver(0)
                except Exception as e:
                    logger.warning(f"No se pudo desconectar driver del kernel: {e}")
            
            # Configurar dispositivo
            self.device.set_configuration()
            
            # Encontrar interfaz PTP
            cfg = self.device.get_active_configuration()
            interface = None
            
            for intf in cfg:
                # Buscar interfaz PTP (Still Image Capture)
                if intf.bInterfaceClass == 6:  # Still Image Capture
                    interface = intf
                    self.interface_number = intf.bInterfaceNumber
                    break
            
            if not interface:
                logger.error("No se encontró interfaz PTP")
                return False
            
            # Encontrar endpoints
            for endpoint in interface:
                if usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    if endpoint.bmAttributes == usb.util.ENDPOINT_TYPE_BULK:
                        self.endpoint_out = endpoint.bEndpointAddress
                elif usb.util.endpoint_direction(endpoint.bEndpointAddress) == usb.util.ENDPOINT_IN:
                    if endpoint.bmAttributes == usb.util.ENDPOINT_TYPE_BULK:
                        self.endpoint_in = endpoint.bEndpointAddress
                    elif endpoint.bmAttributes == usb.util.ENDPOINT_TYPE_INTR:
                        self.endpoint_interrupt = endpoint.bEndpointAddress
            
            if not self.endpoint_out or not self.endpoint_in:
                logger.error("No se encontraron endpoints necesarios")
                return False
            
            # Inicializar sesión PTP
            if self._open_session():
                self.is_connected = True
                self._get_device_info()
                logger.info("Conexión PTP establecida exitosamente")
                return True
            else:
                logger.error("Error al abrir sesión PTP")
                return False
                
        except Exception as e:
            logger.error(f"Error al conectar con la cámara: {str(e)}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la cámara"""
        try:
            if self.is_connected:
                self._close_session()
                self.is_connected = False
            
            # Reconfigurar dispositivo si es necesario
            try:
                usb.util.dispose_resources(self.device)
            except Exception:
                pass
                
        except Exception as e:
            logger.error(f"Error al desconectar: {str(e)}")
    
    def _get_next_transaction_id(self) -> int:
        """Genera el siguiente ID de transacción"""
        self.transaction_id += 1
        return self.transaction_id
    
    def _send_command(self, opcode: int, params: List[int] = None) -> bool:
        """Envía un comando PTP"""
        try:
            transaction_id = self._get_next_transaction_id()
            container = PTPContainer(
                PTPContainer.CONTAINER_TYPE_COMMAND,
                opcode,
                transaction_id,
                params or []
            )
            
            data = container.pack()
            bytes_written = self.device.write(self.endpoint_out, data, self.timeout)
            
            return bytes_written == len(data)
            
        except Exception as e:
            logger.error(f"Error enviando comando: {str(e)}")
            return False
    
    def _receive_response(self) -> Optional[PTPContainer]:
        """Recibe una respuesta PTP"""
        try:
            # Leer header primero
            header_data = self.device.read(self.endpoint_in, 12, self.timeout)
            if len(header_data) < 12:
                return None
            
            # Obtener longitud total
            total_length = struct.unpack('<I', header_data[:4])[0]
            
            # Leer el resto de los datos si es necesario
            remaining_length = total_length - 12
            remaining_data = b''
            
            if remaining_length > 0:
                remaining_data = self.device.read(self.endpoint_in, remaining_length, self.timeout)
            
            # Construir respuesta completa
            full_data = header_data + remaining_data
            return PTPContainer.unpack(full_data)
            
        except Exception as e:
            logger.error(f"Error recibiendo respuesta: {str(e)}")
            return None
    
    def _open_session(self) -> bool:
        """Abre una sesión PTP"""
        try:
            if self._send_command(PTPOpCode.OPEN_SESSION, [self.session_id]):
                response = self._receive_response()
                return response and response.code == PTPResponseCode.OK
            return False
        except Exception as e:
            logger.error(f"Error abriendo sesión: {str(e)}")
            return False
    
    def _close_session(self) -> bool:
        """Cierra la sesión PTP"""
        try:
            if self._send_command(PTPOpCode.CLOSE_SESSION):
                response = self._receive_response()
                return response and response.code == PTPResponseCode.OK
            return False
        except Exception as e:
            logger.error(f"Error cerrando sesión: {str(e)}")
            return False
    
    def _get_device_info(self) -> bool:
        """Obtiene información del dispositivo"""
        try:
            if self._send_command(PTPOpCode.GET_DEVICE_INFO):
                response = self._receive_response()
                if response and response.code == PTPResponseCode.OK:
                    # Procesar datos de información del dispositivo
                    # (Implementación simplificada)
                    self.device_info = {
                        'vendor_id': self.device.idVendor,
                        'product_id': self.device.idProduct,
                        'ptp_version': 'Unknown',
                        'supported_operations': []
                    }
                    return True
            return False
        except Exception as e:
            logger.error(f"Error obteniendo información del dispositivo: {str(e)}")
            return False
    
    def capture_image(self) -> bool:
        """Captura una imagen"""
        try:
            if not self.is_connected:
                logger.error("No hay conexión con la cámara")
                return False
            
            if self._send_command(PTPOpCode.INITIATE_CAPTURE):
                response = self._receive_response()
                return response and response.code == PTPResponseCode.OK
            return False
        except Exception as e:
            logger.error(f"Error capturando imagen: {str(e)}")
            return False
    
    def get_property_value(self, property_code: int) -> Optional[Any]:
        """Obtiene el valor de una propiedad del dispositivo"""
        try:
            if self._send_command(PTPOpCode.GET_DEVICE_PROP_VALUE, [property_code]):
                response = self._receive_response()
                if response and response.code == PTPResponseCode.OK:
                    # Procesar datos de la propiedad
                    return response.data
            return None
        except Exception as e:
            logger.error(f"Error obteniendo propiedad: {str(e)}")
            return None
    
    def set_property_value(self, property_code: int, value: Any) -> bool:
        """Establece el valor de una propiedad del dispositivo"""
        try:
            # Preparar datos de la propiedad (implementación simplificada)
            if isinstance(value, int):
                property_data = struct.pack('<I', value)
            elif isinstance(value, str):
                property_data = value.encode('utf-8') + b'\x00'
            else:
                property_data = bytes(value)
            
            # Enviar comando con datos
            transaction_id = self._get_next_transaction_id()
            
            # Primero enviar comando
            if self._send_command(PTPOpCode.SET_DEVICE_PROP_VALUE, [property_code]):
                # Luego enviar datos
                data_container = PTPContainer(
                    PTPContainer.CONTAINER_TYPE_DATA,
                    PTPOpCode.SET_DEVICE_PROP_VALUE,
                    transaction_id
                )
                data_container.data = property_data
                
                data_packet = data_container.pack()
                self.device.write(self.endpoint_out, data_packet, self.timeout)
                
                # Recibir respuesta
                response = self._receive_response()
                return response and response.code == PTPResponseCode.OK
            
            return False
        except Exception as e:
            logger.error(f"Error estableciendo propiedad: {str(e)}")
            return False

# Función auxiliar para testear la conexión
def test_ptp_connection():
    """Función de prueba para verificar conexión PTP"""
    from camera_usb_detector import USBCameraDetector
    
    detector = USBCameraDetector()
    cameras = detector.scan_for_cameras()
    
    if not cameras:
        print("No se encontraron cámaras")
        return
    
    # Probar con la primera cámara encontrada
    camera = cameras[0]
    print(f"Probando conexión con: {camera['model']}")
    
    try:
        controller = BasePTPController(camera['device_object'])
        
        if controller.connect():
            print("✓ Conexión PTP establecida")
            print(f"Información del dispositivo: {controller.device_info}")
            
            # Probar captura
            print("Intentando capturar imagen...")
            if controller.capture_image():
                print("✓ Comando de captura enviado")
            else:
                print("✗ Error en comando de captura")
            
            controller.disconnect()
            print("✓ Desconexión exitosa")
        else:
            print("✗ Error al establecer conexión PTP")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_ptp_connection()