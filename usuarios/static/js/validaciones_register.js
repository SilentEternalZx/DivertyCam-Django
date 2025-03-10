function verificar_usuario() {
    let username = document.getElementById("username").value.trim();
    let errorContainer = document.getElementById("error-container");

    if (username === "") return;

    fetch(`/usuarios/verificar_usuario/?username=${username}`)
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
                errorContainer.style.display = "none";
            }
        })
        .catch(error => {
            console.error("❌ Error en la verificación del usuario:", error);
            errorContainer.style.display = "block";
            errorContainer.innerHTML = "⚠️ Error al verificar el usuario.";
        });
}


function verificar_password() {
    let password = document.getElementById("password1").value;
    let confirmPassword = document.getElementById("password2").value;
    let errorContainer = document.getElementById("error-container");
    let errores = [];

    let regexMayuscula = /[A-Z]/;
    let regexMinuscula = /[a-z]/;
    let regexNumero = /\d/;
    let regexEspecial = /[!@#$%^&*(),.?":{}|<>]/;

    if (password.length < 8 || password.length > 20) {
        errores.push("⚠️ La contraseña debe tener entre 8 y 20 caracteres.");
    }
    if (!regexMayuscula.test(password)) {
        errores.push("⚠️ Debe incluir al menos una mayúscula.");
    }
    if (!regexMinuscula.test(password)) {
        errores.push("⚠️ Debe incluir al menos una minúscula.");
    }
    if (!regexNumero.test(password)) {
        errores.push("⚠️ Debe incluir al menos un número.");
    }
    if (!regexEspecial.test(password)) {
        errores.push("⚠️ Debe incluir al menos un carácter especial (!@#$%^&*()).");
    }
    if (/^\d+$/.test(password)) {
        errores.push("⚠️ La contraseña no puede ser solo números.");
    }
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

    if (username === "") errores.push("⚠️ El nombre de usuario es obligatorio.");
    if (email === "") errores.push("⚠️ El correo electrónico es obligatorio.");
    if (password === "") errores.push("⚠️ La contraseña es obligatoria.");
    if (confirmPassword === "") errores.push("⚠️ Debes confirmar la contraseña.");

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

    if (email === "") return;

    fetch(`/usuarios/verificar_email/?email=${email}`)
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
                errorContainer.style.display = "none";
            }
        })
        .catch(error => {
            console.error("❌ Error en la verificación del email:", error);
            errorContainer.style.display = "block";
            errorContainer.innerHTML = "⚠️ Error al verificar el email.";
        });
}

