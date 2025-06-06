document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.getElementById('form');
  const inputs = document.querySelectorAll('#form input, #form select');

  const expresiones = {
    nombre: /^[a-zA-ZÀ-ÿ\s]{3,50}$/,
    apellido: /^[a-zA-ZÀ-ÿ\s]{3,50}$/,
    cedula: /^\d{5,20}$/,
    fechaNacimiento: /^\d{4}-\d{2}-\d{2}$/,
    direccion: /^.{5,50}$/,
    telefono: /^\d{9,15}$/,
    
  };

  const mensajes = {
    nombre: "El nombre debe tener entre 3 y 50 letras, sin números.",
    apellido: "El apellido debe tener entre 3 y 50 letras, sin números.",
    cedula: "La cédula debe tener al menos 5 dígitos.",
    fechaNacimiento: "Debes tener al menos 18 años.",
    direccion: "La dirección debe tener al menos 5 caracteres.",
    telefono: "El número de teléfono debe estar en formato: '+999999999'. Hasta 15 dígitos permitidos.",
    
  };

  const campos = {
    nombre: false,
    apellido: false,
    cedula: false,
    fechaNacimiento: false,
    direccion: false,
    telefono: false,
    usuario: false
  };

  function calcularEdad(fecha) {
    const hoy = new Date();
    const nacimiento = new Date(fecha);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const m = hoy.getMonth() - nacimiento.getMonth();
    if (m < 0 || (m === 0 && hoy.getDate() < nacimiento.getDate())) {
      edad--;
    }
    return edad;
  }

  function validarFormulario(e) {
    const field = e.target.name;
    const value = e.target.value.trim();
    const errorDiv = document.getElementById(`error-${field}`);

    // Validación de campo vacío
    if (value === "") {
      errorDiv.textContent = "Este campo no puede estar vacío.";
      e.target.classList.add('is-invalid');
      e.target.classList.remove('is-valid');
      campos[field] = false;
      return;
    }

    // Solo letras para nombre y apellido
    if ((field === "nombre" || field === "apellido") && /\d/.test(value)) {
      errorDiv.textContent = "Este campo no puede contener números.";
      e.target.classList.add('is-invalid');
      e.target.classList.remove('is-valid');
      campos[field] = false;
      return;
    }

    if ((field==="telefono") && !/^\d+$/.test(value)) {
        errorDiv.textContent = "El teléfono solo puede contener números.";
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        campos[field] = false;
        return;
    }

     if ((field==="cedula") && !/^\d+$/.test(value)) {
        errorDiv.textContent = "La cédula solo puede contener números.";
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        campos[field] = false;
        return;
    }


    // Validación por expresión regular
    if (expresiones[field] && !expresiones[field].test(value)) {
      errorDiv.textContent = mensajes[field];
      e.target.classList.add('is-invalid');
      e.target.classList.remove('is-valid');
      campos[field] = false;
      return;
    }

    // Validación de edad para fechaNacimiento
    if (field === "fechaNacimiento") {
      if (calcularEdad(value) < 18) {
        errorDiv.textContent = mensajes[field];
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        campos[field] = false;
        return;
      }
    }

    // Si pasa todas las validaciones
    errorDiv.textContent = "";
    e.target.classList.remove('is-invalid');
    e.target.classList.add('is-valid');
    campos[field] = true;
  }

  inputs.forEach((input) => {
    input.addEventListener('keyup', validarFormulario);
    input.addEventListener('blur', validarFormulario);
  });

  // Validación al enviar
  formulario.addEventListener('submit', function(e) {
    // Disparar validación para todos los campos por si no los tocaron
    inputs.forEach(input => {
      input.dispatchEvent(new Event('blur'));
    });

    // Si algún campo es false, evitar submit
    if (Object.values(campos).includes(false)) {
      e.preventDefault();
      alert('Por favor, completa todos los campos correctamente.');
    }
  });
});