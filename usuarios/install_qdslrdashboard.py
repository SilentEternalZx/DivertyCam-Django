#  archivo: install_qdslrdashboard.py

import os
import sys
import urllib.request
import zipfile
import platform

def download_qdslrdashboard():
    """Descargar e instalar qDslrDashboard"""
    
    print("=== Instalador de qDslrDashboard ===\n")
    
    # URL de descarga (actualizar según versión)
    if platform.system() == 'Windows':
        if platform.machine().endswith('64'):
            download_url = "https://dslrdashboard.info/downloads/qDslrDashboard_V3.6.4_Windows_x64.zip"
            filename = "qDslrDashboard_x64.zip"
        else:
            download_url = "https://dslrdashboard.info/downloads/qDslrDashboard_V3.6.4_Windows_x86.zip"
            filename = "qDslrDashboard_x86.zip"
    else:
        print("Este instalador es solo para Windows")
        return False
    
    try:
        # Descargar
        print(f"Descargando desde {download_url}...")
        urllib.request.urlretrieve(download_url, filename)
        
        # Extraer
        print("Extrayendo archivos...")
        install_path = r"C:\Program Files\qDslrDashboard"
        os.makedirs(install_path, exist_ok=True)
        
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(install_path)
        
        # Limpiar
        os.remove(filename)
        
        print(f"\n✓ qDslrDashboard instalado en: {install_path}")
        print("\nPara usar con el photobooth:")
        print("1. Conecta tu cámara Nikon")
        print("2. El sistema iniciará automáticamente el servidor")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error durante la instalación: {e}")
        return False

if __name__ == "__main__":
    download_qdslrdashboard()