// usb_camera_integration.js
// JavaScript para integración de cámaras USB en el photobooth

class USBCameraController {
    constructor() {
        this.isInitialized = false;
        this.connectedCameras = new Map();
        this.availableCameras = [];
        this.currentSession = null;
        this.detectionInterval = null;
        
        // URLs de la API
        this.apiUrls = {
            detect: '/api/usb/cameras/detect/',
            connect: '/api/usb/cameras/connect/',
            disconnect: '/api/usb/cameras/disconnect/',
            capture: '/api/usb/cameras/capture/',
            setSetting: '/api/usb/cameras/setting/set/',
            getSetting: '/api/usb/cameras/setting/get/',
            status: '/api/usb/cameras/status/'
        };
        
        this.init();
    }
    
    async init() {
        console.log('🔌 Inicializando controlador USB...');
        
        try {
            // Detectar cámaras disponibles
            await this.detectCameras();
            
            // Configurar detección periódica
            this.startPeriodicDetection();
            
            // Configurar event listeners
            this.setupEventListeners();
            
            this.isInitialized = true;
            console.log('✅ Controlador USB inicializado');
            
            // Disparar evento de inicialización
            this.dispatchEvent('usb-controller-initialized', {
                availableCameras: this.availableCameras
            });
            
        } catch (error) {
            console.error('❌ Error inicializando controlador USB:', error);
            this.showError('Error inicializando sistema de cámaras USB');
        }
    }
    
    async detectCameras() {
        console.log('🔍 Detectando cámaras USB...');
        
        try {
            const response = await fetch(this.apiUrls.detect, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                const previousCount = this.availableCameras.length;
                this.availableCameras = data.cameras;
                
                console.log(`📷 Detectadas ${data.count} cámaras USB`);
                
                // Actualizar UI si hay cambios
                if (previousCount !== data.count) {
                    this.updateCameraList();
                    this.dispatchEvent('cameras-detected', {
                        cameras: this.availableCameras,
                        count: data.count
                    });
                }
                
                return this.availableCameras;
            } else {
                throw new Error(data.error || 'Error detectando cámaras');
            }
            
        } catch (error) {
            console.error('Error detectando cámaras:', error);
            this.showError(`Error detectando cámaras: ${error.message}`);
            return [];
        }
    }
    
    async connectCamera(cameraId, eventoId = null) {
        console.log(`🔗 Conectando cámara: ${cameraId}`);
        
        try {
            const response = await fetch(this.apiUrls.connect, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    camera_id: cameraId,
                    evento_id: eventoId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.connectedCameras.set(cameraId, {
                    sessionId: data.session_id,
                    cameraInfo: data.camera_info,
                    deviceInfo: data.device_info,
                    connectedAt: new Date()
                });
                
                console.log('✅ Cámara conectada exitosamente');
                
                // Actualizar UI
                this.updateConnectionStatus(cameraId, 'connected');
                
                // Disparar evento
                this.dispatchEvent('camera-connected', {
                    cameraId: cameraId,
                    sessionId: data.session_id,
                    cameraInfo: data.camera_info
                });
                
                return data;
            } else {
                throw new Error(data.error || 'Error conectando cámara');
            }
            
        } catch (error) {
            console.error('Error conectando cámara:', error);
            this.showError(`Error conectando cámara: ${error.message}`);
            this.updateConnectionStatus(cameraId, 'error');
            return null;
        }
    }
    
    async disconnectCamera(sessionId = null) {
        sessionId = sessionId || this.currentSession;
        
        if (!sessionId) {
            console.warn('No hay sesión activa para desconectar');
            return false;
        }
        
        console.log(`🔌 Desconectando cámara (sesión: ${sessionId})`);
        
        try {
            const response = await fetch(this.apiUrls.disconnect, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Limpiar datos locales
                for (let [cameraId, cameraData] of this.connectedCameras.entries()) {
                    if (cameraData.sessionId === sessionId) {
                        this.connectedCameras.delete(cameraId);
                        this.updateConnectionStatus(cameraId, 'disconnected');
                        break;
                    }
                }
                
                if (this.currentSession === sessionId) {
                    this.currentSession = null;
                }
                
                console.log('✅ Cámara desconectada exitosamente');
                
                this.dispatchEvent('camera-disconnected', {
                    sessionId: sessionId
                });
                
                return true;
            } else {
                throw new Error(data.error || 'Error desconectando cámara');
            }
            
        } catch (error) {
            console.error('Error desconectando cámara:', error);
            this.showError(`Error desconectando cámara: ${error.message}`);
            return false;
        }
    }
    
    async capturePhoto(sessionId = null) {
        sessionId = sessionId || this.currentSession;
        
        if (!sessionId) {
            this.showError('No hay cámara conectada');
            return null;
        }
        
        console.log('📸 Capturando foto...');
        
        try {
            // Mostrar indicador de captura
            this.showCaptureIndicator(true);
            
            const response = await fetch(this.apiUrls.capture, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_id: sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('✅ Foto capturada exitosamente');
                
                this.dispatchEvent('photo-captured', {
                    sessionId: sessionId,
                    timestamp: data.timestamp,
                    data: data
                });
                
                return data;
            } else {
                throw new Error(data.error || 'Error capturando foto');
            }
            
        } catch (error) {
            console.error('Error capturando foto:', error);
            this.showError(`Error capturando foto: ${error.message}`);
            return null;
        } finally {
            this.showCaptureIndicator(false);
        }
    }
    
    async setCameraSetting(settingName, value, sessionId = null) {
        sessionId = sessionId || this.currentSession;
        
        if (!sessionId) {
            console.warn('No hay cámara conectada para configurar');
            return false;
        }
        
        console.log(`⚙️ Configurando ${settingName} = ${value}`);
        
        try {
            const response = await fetch(this.apiUrls.setSetting, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    setting_name: settingName,
                    setting_value: value
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✅ Configuración ${settingName} aplicada`);
                
                this.dispatchEvent('setting-changed', {
                    sessionId: sessionId,
                    settingName: settingName,
                    value: value
                });
                
                return true;
            } else {
                throw new Error(data.error || 'Error configurando cámara');
            }
            
        } catch (error) {
            console.error(`Error configurando ${settingName}:`, error);
            this.showError(`Error configurando ${settingName}: ${error.message}`);
            return false;
        }
    }
    
    async getCameraSetting(settingName, sessionId = null) {
        sessionId = sessionId || this.currentSession;
        
        if (!sessionId) {
            console.warn('No hay cámara conectada para consultar');
            return null;
        }
        
        try {
            const url = new URL(this.apiUrls.getSetting, window.location.origin);
            url.searchParams.append('session_id', sessionId);
            url.searchParams.append('setting_name', settingName);
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (data.success) {
                return data.value;
            } else {
                throw new Error(data.error || 'Error obteniendo configuración');
            }
            
        } catch (error) {
            console.error(`Error obteniendo ${settingName}:`, error);
            return null;
        }
    }
    
    startPeriodicDetection(interval = 5000) {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        this.detectionInterval = setInterval(() => {
            this.detectCameras();
        }, interval);
        
        console.log(`🔄 Detección periódica iniciada (${interval}ms)`);
    }
    
    stopPeriodicDetection() {
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
            console.log('⏹️ Detección periódica detenida');
        }
    }
    
    updateCameraList() {
        // Actualizar selector de cámaras USB
        const usbCameraSelect = document.getElementById('usb-camera-select');
        if (usbCameraSelect) {
            usbCameraSelect.innerHTML = '<option value="">-- Seleccionar cámara USB --</option>';
            
            this.availableCameras.forEach(camera => {
                const option = document.createElement('option');
                option.value = camera.id;
                option.textContent = `${camera.model}${camera.serial_number ? ` (${camera.serial_number})` : ''}`;
                option.dataset.vendor = camera.vendor_name;
                option.dataset.product = camera.product_name;
                usbCameraSelect.appendChild(option);
            });
        }
        
        // Actualizar lista de cámaras detectadas
        const cameraListContainer = document.getElementById('usb-cameras-list');
        if (cameraListContainer) {
            cameraListContainer.innerHTML = '';
            
            if (this.availableCameras.length === 0) {
                cameraListContainer.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> No se detectaron cámaras USB compatibles.
                    </div>
                `;
            } else {
                this.availableCameras.forEach(camera => {
                    const cameraCard = this.createCameraCard(camera);
                    cameraListContainer.appendChild(cameraCard);
                });
            }
        }
    }
    
    createCameraCard(camera) {
        const card = document.createElement('div');
        card.className = 'list-group-item';
        card.dataset.cameraId = camera.id;
        
        const isConnected = this.connectedCameras.has(camera.id);
        const statusClass = isConnected ? 'success' : 'secondary';
        const statusText = isConnected ? 'Conectada' : 'Disponible';
        const buttonText = isConnected ? 'Desconectar' : 'Conectar';
        const buttonAction = isConnected ? 'disconnect' : 'connect';
        
        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1">${camera.model}</h6>
                    <small class="text-muted">
                        ${camera.vendor_name} | ${camera.id}
                        ${camera.serial_number ? `| S/N: ${camera.serial_number}` : ''}
                    </small>
                </div>
                <div class="text-end">
                    <span class="badge bg-${statusClass} mb-2">${statusText}</span><br>
                    <button type="button" 
                            class="btn btn-${isConnected ? 'danger' : 'primary'} btn-sm"
                            data-action="${buttonAction}"
                            data-camera-id="${camera.id}">
                        <i class="fas fa-${isConnected ? 'unlink' : 'link'}"></i> ${buttonText}
                    </button>
                </div>
            </div>
        `;
        
        // Añadir event listener al botón
        const button = card.querySelector('button');
        button.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            const cameraId = e.target.dataset.cameraId;
            
            if (action === 'connect') {
                this.connectCamera(cameraId, window.EVENTO_ID);
            } else if (action === 'disconnect') {
                const cameraData = this.connectedCameras.get(cameraId);
                if (cameraData) {
                    this.disconnectCamera(cameraData.sessionId);
                }
            }
        });
        
        return card;
    }
    
    updateConnectionStatus(cameraId, status) {
        const card = document.querySelector(`[data-camera-id="${cameraId}"]`);
        if (!card) return;
        
        const badge = card.querySelector('.badge');
        const button = card.querySelector('button');
        
        if (badge && button) {
            switch (status) {
                case 'connected':
                    badge.className = 'badge bg-success mb-2';
                    badge.textContent = 'Conectada';
                    button.className = 'btn btn-danger btn-sm';
                    button.innerHTML = '<i class="fas fa-unlink"></i> Desconectar';
                    button.dataset.action = 'disconnect';
                    break;
                    
                case 'disconnected':
                    badge.className = 'badge bg-secondary mb-2';
                    badge.textContent = 'Disponible';
                    button.className = 'btn btn-primary btn-sm';
                    button.innerHTML = '<i class="fas fa-link"></i> Conectar';
                    button.dataset.action = 'connect';
                    break;
                    
                case 'connecting':
                    badge.className = 'badge bg-warning mb-2';
                    badge.textContent = 'Conectando...';
                    button.disabled = true;
                    break;
                    
                case 'error':
                    badge.className = 'badge bg-danger mb-2';
                    badge.textContent = 'Error';
                    button.disabled = false;
                    break;
            }
        }
    }
    
    setupEventListeners() {
        // Event listener para cambio de tipo de cámara
        const tipoCamaraSelect = document.getElementById('tipo-camara');
        if (tipoCamaraSelect) {
            tipoCamaraSelect.addEventListener('change', (e) => {
                this.handleCameraTypeChange(e.target.value);
            });
        }
        
        // Event listener para botón de detectar cámaras
        const detectButton = document.getElementById('detect-usb-cameras-btn');
        if (detectButton) {
            detectButton.addEventListener('click', () => {
                this.detectCameras();
            });
        }
        
        // Event listener para selector de cámaras USB
        const usbCameraSelect = document.getElementById('usb-camera-select');
        if (usbCameraSelect) {
            usbCameraSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.connectCamera(e.target.value, window.EVENTO_ID);
                }
            });
        }
    }
    
    handleCameraTypeChange(cameraType) {
        const usbSection = document.getElementById('usb-camera-section');
        
        if (usbSection) {
            if (['usb_ptp', 'canon_dslr', 'sony_camera'].includes(cameraType)) {
                usbSection.style.display = 'block';
                // Detectar cámaras automáticamente al cambiar a USB
                this.detectCameras();
            } else {
                usbSection.style.display = 'none';
                // Desconectar cámaras USB si hay alguna conectada
                if (this.currentSession) {
                    this.disconnectCamera();
                }
            }
        }
        
        // Mostrar/ocultar campos USB en el formulario
        const usbFields = document.querySelectorAll('[data-camera-types]');
        usbFields.forEach(field => {
            const supportedTypes = field.dataset.cameraTypes.split(',');
            if (supportedTypes.includes(cameraType)) {
                field.closest('.mb-3')?.style.setProperty('display', 'block');
            } else {
                field.closest('.mb-3')?.style.setProperty('display', 'none');
            }
        });
    }
    
    showCaptureIndicator(show) {
        const indicator = document.getElementById('capture-indicator');
        if (indicator) {
            indicator.style.display = show ? 'block' : 'none';
        }
        
        // También podemos añadir un overlay temporal
        if (show) {
            const overlay = document.createElement('div');
            overlay.id = 'capture-overlay';
            overlay.className = 'capture-overlay';
            overlay.innerHTML = `
                <div class="capture-animation">
                    <i class="fas fa-camera fa-3x"></i>
                    <p>Capturando...</p>
                </div>
            `;
            document.body.appendChild(overlay);
            
            // Remover después de 2 segundos
            setTimeout(() => {
                const overlay = document.getElementById('capture-overlay');
                if (overlay) overlay.remove();
            }, 2000);
        }
    }
    
    showError(message) {
        console.error('USB Camera Error:', message);
        
        // Mostrar error en la UI
        const errorContainer = document.getElementById('usb-camera-errors');
        if (errorContainer) {
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger alert-dismissible fade show';
            alert.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            errorContainer.appendChild(alert);
            
            // Auto-remover después de 5 segundos
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 5000);
        }
    }
    
    dispatchEvent(eventName, detail) {
        const event = new CustomEvent(`usb-camera-${eventName}`, {
            detail: detail,
            bubbles: true
        });
        document.dispatchEvent(event);
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        
        if (cookieValue) {
            return cookieValue.split('=')[1];
        }
        
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) {
            return csrfInput.value;
        }
        
        return '';
    }
    
    // Métodos públicos para integración con photobooth
    isConnected() {
        return this.currentSession !== null;
    }
    
    getConnectedCamera() {
        if (this.currentSession) {
            for (let [cameraId, cameraData] of this.connectedCameras.entries()) {
                if (cameraData.sessionId === this.currentSession) {
                    return cameraData;
                }
            }
        }
        return null;
    }
    
    async quickCapture() {
        if (!this.isConnected()) {
            throw new Error('No hay cámara USB conectada');
        }
        
        return await this.capturePhoto();
    }
    
    destroy() {
        this.stopPeriodicDetection();
        
        // Desconectar todas las cámaras
        for (let [cameraId, cameraData] of this.connectedCameras.entries()) {
            this.disconnectCamera(cameraData.sessionId);
        }
        
        console.log('🗑️ Controlador USB destruido');
    }
}

// CSS para efectos visuales
const usbCameraCSS = `
.capture-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
    animation: fadeIn 0.3s ease-in;
}

.capture-animation {
    text-align: center;
    color: white;
    animation: pulse 1s ease-in-out infinite;
}

.capture-animation i {
    display: block;
    margin-bottom: 20px;
    animation: flash 0.1s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

@keyframes flash {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

#usb-camera-section {
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 1rem;
    margin-top: 1rem;
}

.usb-camera-status {
    padding: 0.5rem;
    margin: 0.5rem 0;
    border-radius: 0.25rem;
    font-size: 0.875rem;
}

.usb-camera-status.connected {
    background-color: #d1edff;
    border: 1px solid #0084ff;
    color: #0066cc;
}

.usb-camera-status.disconnected {
    background-color: #f8f9fa;
    border: 1px solid #6c757d;
    color: #495057;
}
`;

// Añadir CSS al documento
if (!document.getElementById('usb-camera-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'usb-camera-styles';
    styleSheet.textContent = usbCameraCSS;
    document.head.appendChild(styleSheet);
}

// Inicializar controlador cuando se carga el DOM
let usbCameraController = null;

document.addEventListener('DOMContentLoaded', function() {
    // Solo inicializar si estamos en una página que lo necesite
    if (document.getElementById('tipo-camara') || document.querySelector('[data-usb-camera]')) {
        usbCameraController = new USBCameraController();
        
        // Hacer disponible globalmente
        window.usbCameraController = usbCameraController;
    }
});

// Limpiar al salir
window.addEventListener('beforeunload', function() {
    if (usbCameraController) {
        usbCameraController.destroy();
    }
});

// Event listeners para integración con photobooth
document.addEventListener('usb-camera-photo-captured', function(event) {
    console.log('📸 Foto USB capturada:', event.detail);
    
    // Integrar con el sistema de photobooth existente
    if (typeof handleCapturedPhoto === 'function') {
        handleCapturedPhoto(event.detail);
    }
});

document.addEventListener('usb-camera-camera-connected', function(event) {
    console.log('🔗 Cámara USB conectada:', event.detail);
    
    // Actualizar UI del photobooth
    const cameraInfo = document.getElementById('camera-info');
    if (cameraInfo) {
        cameraInfo.innerHTML = `
            <strong>Cámara conectada:</strong><br>
            ${event.detail.cameraInfo.model}<br>
            <small class="text-muted">Sesión: ${event.detail.sessionId}</small>
        `;
        cameraInfo.style.display = 'block';
    }
});

// Funciones helper para integración con el sistema existente
function updateCameraTypeSection() {
    currentCameraType = tipoCamaraSelect ? tipoCamaraSelect.value : 'webcam';
    console.log('Tipo de cámara seleccionado:', currentCameraType);
    
    // Detener cualquier preview activo
    stopAllPreviews();
    
    // Ocultar todas las secciones primero
    if (webcamSection) webcamSection.style.display = 'none';
    if (document.getElementById('usb-section')) document.getElementById('usb-section').style.display = 'none';
    if (document.getElementById('nikon-section')) document.getElementById('nikon-section').style.display = 'none';
    
    // Mostrar la sección correspondiente
    switch(currentCameraType) {
        case 'webcam':
            if (webcamSection) webcamSection.style.display = 'block';
            listAvailableCameras();
            break;
            
        case 'windows_camera':
        case 'usb_ptp':
            if (document.getElementById('usb-section')) {
                document.getElementById('usb-section').style.display = 'block';
            }
            // Detectar cámaras USB si está disponible
            if (window.usbCameraController) {
                window.usbCameraController.detectCameras();
            }
            break;
            
        case 'nikon_dslr':
            if (document.getElementById('nikon-section')) {
                document.getElementById('nikon-section').style.display = 'block';
            }
            break;
    }
}

function captureUSBPhoto() {
    if (usbCameraController && usbCameraController.isConnected()) {
        return usbCameraController.quickCapture();
    } else {
        throw new Error('No hay cámara USB conectada');
    }
}

function getUSBCameraStatus() {
    if (usbCameraController) {
        return {
            isConnected: usbCameraController.isConnected(),
            connectedCamera: usbCameraController.getConnectedCamera(),
            availableCameras: usbCameraController.availableCameras
        };
    }
    return null;
}