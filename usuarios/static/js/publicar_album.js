function publicarAlbum(eventoId) {
    let mensajeElemento = document.getElementById("mensaje-publicacion");

    fetch(`/usuarios/publicar_album/${eventoId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "Content-Type": "application/json"
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            mensajeElemento.innerHTML = "✅ Álbum publicado en Facebook";
            mensajeElemento.style.color = "green";
        } else {
            mensajeElemento.innerHTML = "❌ Error al publicar";
            mensajeElemento.style.color = "red";
        }
    })
    .catch(error => {
        mensajeElemento.innerHTML = "❌ Error inesperado";
        mensajeElemento.style.color = "red";
    });
}

// 📌 Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
