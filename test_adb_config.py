# test_adb_config.py
# Script para probar la configuración de ADB

import subprocess
import os

def test_adb():
    adb_path = r'C:\Users\DELL\AppData\Local\Android\Sdk\platform-tools\adb.exe'
    
    print("🧪 Probando configuración de ADB...")
    print("=" * 50)
    
    # 1. Verificar que ADB existe
    if os.path.exists(adb_path):
        print(f"✅ ADB encontrado: {adb_path}")
    else:
        print(f"❌ ADB NO encontrado: {adb_path}")
        return False
    
    # 2. Probar versión de ADB
    try:
        result = subprocess.run([adb_path, 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ ADB funciona: {version}")
        else:
            print(f"❌ Error en ADB: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando ADB: {e}")
        return False
    
    # 3. Verificar dispositivos conectados
    try:
        result = subprocess.run([adb_path, 'devices'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            print(f"\n📱 Estado de dispositivos:")
            for line in lines:
                print(f"   {line}")
            
            # Contar dispositivos conectados
            devices = [line for line in lines[1:] if '\tdevice' in line]
            if devices:
                print(f"✅ {len(devices)} dispositivo(s) Android conectado(s) y listo(s)")
                return True
            else:
                print("⚠️  No hay dispositivos Android conectados")
                print("   Instrucciones:")
                print("   1. Conecta tu dispositivo Android por cable USB")
                print("   2. Habilita 'Opciones de desarrollador' en Android")
                print("   3. Activa 'Depuración USB'")
                print("   4. Autoriza la conexión cuando aparezca el diálogo")
                return False
        else:
            print(f"❌ Error verificando dispositivos: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_django_import():
    print("\n🧪 Probando importación en Django...")
    print("=" * 50)
    
    try:
        # Simular la importación como lo haría Django
        import sys
        import os
        
        # Agregar el directorio del proyecto al path
        project_dir = os.getcwd()
        if project_dir not in sys.path:
            sys.path.append(project_dir)
        
        # Intentar importar el módulo
        from usuarios.utils.usb_communication import USBCommunication
        
        print("✅ Importación exitosa de USBCommunication")
        
        # Probar instanciación
        usb = USBCommunication()
        print("✅ Instanciación exitosa")
        
        # Probar método
        connected, devices = usb.check_device_connected()
        if connected:
            print(f"✅ Dispositivos detectados: {len(devices)}")
        else:
            print("⚠️  No hay dispositivos conectados (esto es normal si no tienes Android conectado)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate de crear el archivo usuarios/utils/usb_communication.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Probador de configuración ADB + Django")
    print("=" * 60)
    
    adb_ok = test_adb()
    django_ok = test_django_import()
    
    print("\n" + "=" * 60)
    if adb_ok and django_ok:
        print("🎉 ¡Configuración completada exitosamente!")
        print("📱 Tu sistema está listo para enviar collages por WhatsApp")
    elif adb_ok:
        print("⚠️  ADB funciona pero hay problemas con Django")
        print("   Revisa que hayas creado todos los archivos necesarios")
    else:
        print("❌ Hay problemas con la configuración")
        print("   Revisa los errores mostrados arriba")
    
    print("\n📋 Próximos pasos:")
    print("1. Conectar dispositivo Android (si no está conectado)")
    print("2. Instalar app Android en el dispositivo")
    print("3. Probar el sistema completo")