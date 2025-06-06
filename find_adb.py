# Script para encontrar ADB en instalaciones de Android Studio

import os
import subprocess
from pathlib import Path

def find_adb_paths():
    """Busca ADB en ubicaciones comunes de Android Studio"""
    possible_paths = []
    
    # Ubicaciones comunes
    username = os.getenv('USERNAME')
    common_locations = [
        f"C:\\Users\\{username}\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
        f"C:\\Android\\Sdk\\platform-tools\\adb.exe",
        f"C:\\Program Files\\Android\\Android Studio\\bin\\adb.exe",
        f"C:\\Program Files (x86)\\Android\\Android Studio\\bin\\adb.exe",
    ]
    
    # Verificar cada ubicación
    for path in common_locations:
        if os.path.exists(path):
            possible_paths.append(path)
            print(f"✅ Encontrado: {path}")
        else:
            print(f"❌ No existe: {path}")
    
    # Buscar en variables de entorno
    android_home = os.getenv('ANDROID_HOME')
    if android_home:
        android_home_adb = os.path.join(android_home, 'platform-tools', 'adb.exe')
        if os.path.exists(android_home_adb):
            possible_paths.append(android_home_adb)
            print(f"✅ Encontrado en ANDROID_HOME: {android_home_adb}")
    
    # Buscar en PATH
    try:
        result = subprocess.run(['where', 'adb'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            adb_in_path = result.stdout.strip().split('\n')[0]
            possible_paths.append(adb_in_path)
            print(f"✅ Encontrado en PATH: {adb_in_path}")
    except:
        pass
    
    return possible_paths

def test_adb(adb_path):
    """Prueba si ADB funciona correctamente"""
    try:
        result = subprocess.run([adb_path, 'version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_info = result.stdout.strip()
            print(f"✅ ADB funciona: {version_info}")
            return True
        else:
            print(f"❌ ADB no responde correctamente")
            return False
    except Exception as e:
        print(f"❌ Error probando ADB: {e}")
        return False

def check_device_connection(adb_path):
    """Verifica si hay dispositivos conectados"""
    try:
        result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"\n📱 Estado de dispositivos:")
            for line in lines:
                print(f"   {line}")
            
            # Contar dispositivos conectados
            devices = [line for line in lines[1:] if '\tdevice' in line]
            if devices:
                print(f"✅ {len(devices)} dispositivo(s) conectado(s) y listo(s)")
                return True
            else:
                print("⚠️  No hay dispositivos conectados o no están en modo 'device'")
                print("   Asegúrate de:")
                print("   - Conectar el dispositivo por USB")
                print("   - Habilitar 'Depuración USB' en el dispositivo")
                print("   - Autorizar la conexión en el dispositivo")
                return False
        else:
            print(f"❌ Error ejecutando 'adb devices': {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error verificando dispositivos: {e}")
        return False

def generate_settings_config(adb_path):
    """Genera la configuración para settings.py"""
    # Convertir backslashes para Python strings
    python_path = adb_path.replace('\\', '\\\\')
    
    config = f'''
# ===========================================
# Configuración de ADB para WhatsApp System
# ===========================================

# Ruta a ADB (Android Debug Bridge)
ADB_PATH = r'{adb_path}'

# Configuración USB para transferencias
USB_TRANSFER_CONFIG = {{
    'DEVICE_FOLDER': '/sdcard/photobooth/',
    'TEMP_FOLDER': os.path.join(MEDIA_ROOT, 'temp_usb'),
    'CONNECTION_TIMEOUT': 10,
    'TRANSFER_TIMEOUT': 30,
    'MAX_RETRIES': 3,
}}

# Crear directorio temporal si no existe
import os
TEMP_USB_DIR = os.path.join(MEDIA_ROOT, 'temp_usb')
os.makedirs(TEMP_USB_DIR, exist_ok=True)
'''
    
    return config

def main():
    print("🔍 Buscando ADB en tu sistema...")
    print("=" * 50)
    
    # Buscar ADB
    adb_paths = find_adb_paths()
    
    if not adb_paths:
        print("\n❌ No se encontró ADB en ubicaciones comunes")
        print("Verifica que Android Studio esté correctamente instalado")
        return
    
    print(f"\n📋 Se encontraron {len(adb_paths)} instalación(es) de ADB")
    
    # Probar cada ADB encontrado
    working_adb = None
    for i, adb_path in enumerate(adb_paths, 1):
        print(f"\n🧪 Probando ADB #{i}: {adb_path}")
        if test_adb(adb_path):
            working_adb = adb_path
            break
    
    if not working_adb:
        print("\n❌ Ninguna instalación de ADB funciona correctamente")
        return
    
    print(f"\n✅ ADB funcional encontrado: {working_adb}")
    
    # Verificar conexión de dispositivos
    print(f"\n📱 Verificando dispositivos conectados...")
    device_connected = check_device_connection(working_adb)
    
    # Generar configuración
    print(f"\n📝 Configuración para tu settings.py:")
    print("=" * 50)
    config = generate_settings_config(working_adb)
    print(config)
    
    # Guardar configuración en archivo
    with open('adb_config.txt', 'w') as f:
        f.write(config)
    
    print("=" * 50)
    print(f"✅ Configuración guardada en: adb_config.txt")
    
    if device_connected:
        print("🎉 ¡Todo listo! Tu sistema está configurado para enviar por WhatsApp")
    else:
        print("⚠️  Conecta un dispositivo Android para completar la configuración")
    
    print("\n📋 Próximos pasos:")
    print("1. Copia la configuración a tu settings.py")
    print("2. Crea los archivos utils/usb_communication.py")
    print("3. Conecta dispositivo Android con USB debugging")
    print("4. Instala la app Android en el dispositivo")

if __name__ == "__main__":
    main()