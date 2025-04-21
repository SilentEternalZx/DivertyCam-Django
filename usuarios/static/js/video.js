// Variables para guardar la última imagen capturada
let lastImageUrl = null;
let isChangingCamera = false;
let currentIso = 100; // Valor inicial del ISO

// Función para actualizar el valor mostrado del ISO
function updateIsoValue(value) {
    currentIso = parseInt(value);
    document.getElementById('iso-value').textContent = value;
}

// Función para establecer el ISO en la cámara
function setIso() {
    console.log("ISO que se va a enviar:", currentIso);
    fetch(setIsoUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ iso: currentIso })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('ISO configurado correctamente:', data.iso);
            // Actualizar la interfaz con el valor devuelto por el servidor
            document.getElementById('iso-value').textContent = data.iso;
            // Mostrar un mensaje de éxito
            alert(data.message);
        } else {
            console.error('Error al configurar el ISO:', data.error);
            alert('Error al configurar el ISO: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al comunicarse con el servidor');
    });
}

function updateWhiteBalance(value) {
    fetch("/set_white_balance/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')  // Asegúrate de que esta función esté definida también
        },
        body: JSON.stringify({ white_balance: value })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Balance de blancos actualizado:", data);
    })
    .catch(error => {
        console.error("Error al cambiar el balance de blancos:", error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función para cambiar de cámara
function switchCamera(cameraIndex) {
    if (isChangingCamera) return;
    isChangingCamera = true;
    
    // Mostrar indicador de carga
    const cameraFeed = document.getElementById('camera-feed');
    cameraFeed.style.opacity = '0.5';
    
    fetch('/switch_camera', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ camera_index: cameraIndex })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Cámara cambiada correctamente');
            // Recargar la transmisión de vídeo
            const timestamp = new Date().getTime();
            const cameraFeed = document.getElementById('camera-feed');
            cameraFeed.src = `/video_feed?t=${timestamp}`;
            
            // Restablecer la opacidad después de cargar la nueva transmisión
            cameraFeed.onload = function() {
                cameraFeed.style.opacity = '1';
                isChangingCamera = false;
            };
        } else {
            console.error('Error al cambiar de cámara');
            isChangingCamera = false;
            cameraFeed.style.opacity = '1';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al comunicarse con el servidor');
        isChangingCamera = false;
        cameraFeed.style.opacity = '1';
    });
}

// Función para capturar una imagen
function captureImage() {
    fetch(captureUrl, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Habilitar el botón de descarga
            document.getElementById('download-btn').disabled = false;
            lastImageUrl = data.image_path;
            
            // Recargar la galería para mostrar la nueva imagen
            window.location.reload();
        } else {
            console.error('Error al capturar la imagen:', data.error);
            alert('Error al capturar la imagen: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al comunicarse con el servidor');
    });
}

// Función para descargar la última imagen capturada
function downloadImage() {
    if (lastImageUrl) {
        const link = document.createElement('a');
        link.href = lastImageUrl;
        link.download = lastImageUrl.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        alert('No hay imagen para descargar');
    }
}

