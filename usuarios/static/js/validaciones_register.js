function verificar_username() {
    let username = document.getElementById("username").value.trim();
    let errorContainer = document.getElementById("error-container");
    let errores = [];

    // Validaciones locales (formato y longitud)
    if (username.length < 6 || username.length > 30) {
        errores.push("⚠️ El nombre de usuario debe tener entre 6 y 30 caracteres.");
    }
    if (!/^[\w\s]+$/.test(username)) {
        errores.push("⚠️ El nombre de usuario solo puede contener letras, números y espacios.");
    }
    if (!username) {
        errores.push("⚠️ El nombre de usuario no puede estar vacío.");
    }

    // Si hay errores locales, no consultar al backend
    if (errores.length > 0) {
        errorContainer.style.display = "block";
        errorContainer.innerHTML = errores.join("<br>");
        return false;
    }

    // Si pasa las validaciones, consulta al backend
    fetch(`verificar_usuario/?username=${encodeURIComponent(username)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Error en la respuesta del servidor");
            }
            return response.json();
        })
        .then(data => {
            if (data.existe) {
                errorContainer.style.display = "block";
                errorContainer.innerHTML = "⚠️ Este usuario ya está registrado.";
            } else {
                // Solo ocultar si no hay otros errores
                if (errorContainer.innerHTML.includes("usuario")) {
                    errorContainer.style.display = "none";
                    errorContainer.innerHTML = "";
                }
            }
        })
        .catch(error => {
            console.error("❌ Error en la verificación del usuario:", error);
            errorContainer.style.display = "block";
            errorContainer.innerHTML = "⚠️ Error al verificar el usuario.";
        });

    return true;
}

function verificar_password() {
    let password = document.getElementById("password1").value;
    let confirmPassword = document.getElementById("password2").value;
    let username = document.getElementById("username").value;
    let errorContainer = document.getElementById("error-container");
    let errores = [];

    // Longitud
    if (password.length < 8 || password.length > 15) {
        errores.push("⚠️ La contraseña debe tener entre 8 y 15 caracteres.");
    }

    // No vacío
    if (!password.trim()) {
        errores.push("⚠️ La contraseña no puede estar vacía.");
    }

    // Al menos una letra mayúscula
    if (!/[A-Z]/.test(password)) {
        errores.push("⚠️ La contraseña debe contener al menos una letra mayúscula.");
    }

    // Al menos un número
    if (!/\d/.test(password)) {
        errores.push("⚠️ La contraseña debe contener al menos un número.");
    }

    // Al menos un carácter especial
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        errores.push("⚠️ La contraseña debe contener al menos un carácter especial.");
    }

    // No espacios
    if (/\s/.test(password)) {
        errores.push("⚠️ La contraseña no puede contener espacios.");
    }

    // No puede ser igual al nombre de usuario
    if (username && password.toLowerCase() === username.toLowerCase()) {
        errores.push("⚠️ La contraseña no puede ser igual al nombre de usuario.");
    }

    // No puede contener el nombre de usuario
    if (username && password.toLowerCase().includes(username.toLowerCase())) {
        errores.push("⚠️ La contraseña no puede contener el nombre de usuario.");
    }

    // No puede contener palabras inseguras
    const inseguras = [
        "password", "user", "admin", "1234", "qwerty", "abc", "letmein", "welcome", "iloveyou","hola",
    ];
    for (let palabra of inseguras) {
        if (password.toLowerCase().includes(palabra)) {
            errores.push(`⚠️ La contraseña no puede contener la secuencia '${palabra}'.`);
        }
    }

    // Confirmación
    if (confirmPassword.length > 0 && password !== confirmPassword) {
        errores.push("⚠️ Las contraseñas no coinciden.");
    }

    if (errores.length > 0) {
        errorContainer.style.display = "block";
        errorContainer.innerHTML = errores.join("<br>");
        return false;
    } else {
        errorContainer.style.display = "none";
    }

    return true;
}

function validar_formulario() {
    let username = document.getElementById("username").value.trim();
    let email = document.getElementById("email").value.trim();
    let password = document.getElementById("password1").value.trim();
    let confirmPassword = document.getElementById("password2").value.trim();
    let errorContainer = document.getElementById("error-container");
    let errores = [];

    // Validaciones de campos obligatorios
    if (username === "") errores.push("⚠️ El nombre de usuario es obligatorio.");
    if (email === "") errores.push("⚠️ El correo electrónico es obligatorio.");
    if (password === "") errores.push("⚠️ La contraseña es obligatoria.");
    if (confirmPassword === "") errores.push("⚠️ Debes confirmar la contraseña.");

    // Validaciones específicas
    verificar_username();
    verificar_password();

    if (errorContainer.style.display === "block") {
        errores.push(errorContainer.innerHTML);
    }

    if (errores.length > 0) {
        errorContainer.style.display = "block";
        errorContainer.innerHTML = errores.join("<br>");
        return false;
    }

    setTimeout(() => {
        window.location.href = "/";
    }, 2000);

    return true;
}

function verificar_email() {
    let email = document.getElementById("email").value.trim();
    let errorContainer = document.getElementById("error-container");
    let errores = [];

    // Validación de formato de email
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        errores.push("⚠️ El formato del correo electrónico no es válido.");
    }
    if (!email) {
        errores.push("⚠️ El correo electrónico es obligatorio.");
    }

    // Si hay errores locales, no consultar al backend
    if (errores.length > 0) {
        errorContainer.style.display = "block";
        errorContainer.innerHTML = errores.join("<br>");
        return false;
    }

    // Si pasa las validaciones, consulta al backend
    fetch(`verificar_email/?email=${encodeURIComponent(email)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Error en la respuesta del servidor");
            }
            return response.json();
        })
        .then(data => {
            if (data.existe) {
                errorContainer.style.display = "block";
                errorContainer.innerHTML = "⚠️ Este correo electrónico ya está registrado.";
            } else {
                // Solo ocultar si no hay otros errores
                if (errorContainer.innerHTML.includes("correo electrónico")) {
                    errorContainer.style.display = "none";
                    errorContainer.innerHTML = "";
                }
            }
        })
        .catch(error => {
            console.error("❌ Error en la verificación del email:", error);
            errorContainer.style.display = "block";
            errorContainer.innerHTML = "⚠️ Error al verificar el email.";
        });

    return true;
}


