# Script para configurar el sistema de envío por WhatsApp

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
from pathlib import Path

def check_adb_installation():
    """Verifica si ADB está instalado y accesible"""
    try:
        result = subprocess.run(['adb', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ ADB ya está instalado y accesible")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ ADB no encontrado")
    return False

def download_adb():
    """Descarga ADB si no está disponible"""
    print("📥 Descargando Android Platform Tools...")
    
    # URL para Windows
    url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    tools_dir = Path("android-tools")
    zip_file = "platform-tools.zip"
    
    try:
        # Crear directorio
        tools_dir.mkdir(exist_ok=True)
        
        # Descargar
        urllib.request.urlretrieve(url, zip_file)
        
        # Extraer
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(tools_dir)
        
        # Limpiar
        os.remove(zip_file)
        
        # Obtener ruta de ADB
        adb_path = tools_dir / "platform-tools" / "adb.exe"
        
        if adb_path.exists():
            print(f"✅ ADB descargado en: {adb_path.absolute()}")
            return str(adb_path.absolute())
        else:
            print("❌ Error extrayendo ADB")
            return None
            
    except Exception as e:
        print(f"❌ Error descargando ADB: {e}")
        return None

def create_migration():
    """Crea la migración para el modelo WhatsAppTransfer"""
    migration_content = '''
# Generated migration for WhatsAppTransfer model

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),  # Ajusta según tu última migración
    ]

    operations = [
        migrations.CreateModel(
            name='WhatsAppTransfer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('phone_number', models.CharField(help_text='Número de WhatsApp del usuario', max_length=20, verbose_name='Número de teléfono')),
                ('user_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nombre del usuario')),
                ('user_email', models.EmailField(blank=True, null=True, verbose_name='Email del usuario')),
                ('status', models.CharField(choices=[('sent_to_device', 'Enviado al dispositivo'), ('data_collected', 'Datos recopilados'), ('whatsapp_sent', 'Enviado por WhatsApp'), ('completed', 'Completado'), ('failed', 'Fallido'), ('cancelled', 'Cancelado')], default='sent_to_device', max_length=20, verbose_name='Estado de la transferencia')),
                ('transfer_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Momento de la transferencia')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completado en')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Información adicional sobre la transferencia', verbose_name='Metadatos adicionales')),
                ('device_model', models.CharField(blank=True, max_length=100, null=True, verbose_name='Modelo del dispositivo')),
                ('device_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='ID del dispositivo')),
                ('custom_message', models.TextField(blank=True, help_text='Mensaje personalizado enviado con el collage', null=True, verbose_name='Mensaje personalizado')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Mensaje de error')),
                ('retry_count', models.IntegerField(default=0, verbose_name='Intentos de reenvío')),
                ('collage_result', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_transfers', to='usuarios.collageresult')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_transfers', to='usuarios.collagesession')),
            ],
            options={
                'verbose_name': 'Transferencia de WhatsApp',
                'verbose_name_plural': 'Transferencias de WhatsApp',
                'ordering': ['-transfer_timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='whatsapptransfer',
            index=models.Index(fields=['status'], name='usuarios_wha_status_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsapptransfer',
            index=models.Index(fields=['transfer_timestamp'], name='usuarios_wha_transfe_idx'),
        ),
        migrations.AddIndex(
            model_name='whatsapptransfer',
            index=models.Index(fields=['session'], name='usuarios_wha_session_idx'),
        ),
    ]
'''
    
    # Crear archivo de migración
    migrations_dir = Path("usuarios/migrations")
    migrations_dir.mkdir(exist_ok=True)
    
    # Encontrar el próximo número de migración
    existing_migrations = [f for f in migrations_dir.glob("*.py") if f.name.startswith("0")]
    if existing_migrations:
        last_num = max([int(f.name.split("_")[0]) for f in existing_migrations])
        next_num = f"{last_num + 1:04d}"
    else:
        next_num = "0002"
    
    migration_file = migrations_dir / f"{next_num}_whatsapp_transfer.py"
    
    with open(migration_file, 'w') as f:
        f.write(migration_content)
    
    print(f"✅ Migración creada: {migration_file}")

def create_directories():
    """Crea los directorios necesarios"""
    directories = [
        "media/temp_usb",
        "media/collage/results",
        "logs",
        "usuarios/utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {directory}")

def create_utils_init():
    """Crea el archivo __init__.py en utils"""
    utils_init = Path("usuarios/utils/__init__.py")
    if not utils_init.exists():
        utils_init.touch()
        print("✅ Archivo __init__.py creado en utils")

def test_adb_connection():
    """Prueba la conexión ADB"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            devices = [line for line in lines if '\tdevice' in line]
            
            if devices:
                print(f"✅ {len(devices)} dispositivo(s) Android conectado(s)")
                for device in devices:
                    print(f"   📱 {device}")
            else:
                print("⚠️  ADB funciona pero no hay dispositivos conectados")
                print("   Conecta un dispositivo Android con USB debugging habilitado")
            
            return True
        else:
            print(f"❌ Error ejecutando ADB: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout ejecutando ADB")
        return False
    except FileNotFoundError:
        print("❌ ADB no encontrado en PATH")
        return False

def main():
    print("🚀 Configurando sistema de envío por WhatsApp")
    print("=" * 50)
    
    # 1. Verificar/instalar ADB
    if not check_adb_installation():
        adb_path = download_adb()
        if adb_path:
            print(f"💡 Agrega esta ruta a tu settings.py:")
            print(f"   ADB_PATH = r'{adb_path}'")
        else:
            print("❌ No se pudo configurar ADB")
            return
    
    # 2. Crear directorios
    print("\n📁 Creando directorios...")
    create_directories()
    create_utils_init()
    
    # 3. Crear migración
    print("\n📦 Creando migración de base de datos...")
    create_migration()
    
    # 4. Probar conexión ADB
    print("\n🔌 Probando conexión ADB...")
    test_adb_connection()
    
    print("\n✅ Configuración completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecuta: python manage.py makemigrations")
    print("2. Ejecuta: python manage.py migrate")
    print("3. Agrega las URLs a tu urls.py")
    print("4. Agrega las vistas a tu views.py")
    print("5. Actualiza el JavaScript en session.html")
    print("6. Instala la app Android en el dispositivo móvil")
    print("7. Conecta el dispositivo por USB con USB debugging habilitado")

if __name__ == "__main__":
    main()