document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.getElementById('form');
  const inputs = document.querySelectorAll('#form textarea');
  const fileInput = document.querySelector('#form input[type="file"][name="img"]'); // ← CAMBIO AQUÍ
  const checkboxes = document.querySelectorAll('#form input[type="checkbox"][name="invitados"]');

  const expresiones = {
    descripcion: /^[a-zA-ZÀ-ÿ0-9\s]{5,50}$/,
  };

  const mensajes = {
    descripcion: "La descripción debe contener entre 5 y 50 caracteres",
    img: "Debes subir al menos una imagen.", 
    invitados: "Selecciona al menos un invitado.",
  };

  const campos = {
    descripcion: false,
    img: false,  // ← CAMBIO AQUÍ
    invitados: false,
  };

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

    // Validación por expresión regular
    if (expresiones[field] && !expresiones[field].test(value)) {
      errorDiv.textContent = mensajes[field];
      e.target.classList.add('is-invalid');
      e.target.classList.remove('is-valid');
      campos[field] = false;
      return;
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

  // Validación de imagen
  function validarImagen() {
    const errorDiv = document.getElementById('error-img'); // ← CAMBIO AQUÍ
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      errorDiv.textContent = mensajes.img;
      fileInput?.classList.add('is-invalid');
      fileInput?.classList.remove('is-valid');
      campos.img = false;
    } else {
      errorDiv.textContent = "";
      fileInput.classList.remove('is-invalid');
      fileInput.classList.add('is-valid');
      campos.img = true;
    }
  }
  fileInput?.addEventListener('change', validarImagen);

  // Validación de invitados
  function validarInvitados() {
    const errorDiv = document.getElementById('error-invitados');
    const checked = Array.from(checkboxes).some(cb => cb.checked);
    if (!checked) {
      errorDiv.textContent = mensajes.invitados;
      campos.invitados = false;
    } else {
      errorDiv.textContent = "";
      campos.invitados = true;
    }
  }
  checkboxes.forEach(cb => cb.addEventListener('change', validarInvitados));

  // Validación al enviar
  formulario.addEventListener('submit', function(e) {
    // Disparar validación para todos los campos por si no los tocaron
    inputs.forEach(input => {
      input.dispatchEvent(new Event('blur'));
    });
    validarImagen();
    validarInvitados();

    // Si algún campo es false, evitar submit
    if (Object.values(campos).includes(false)) {
      e.preventDefault();
      alert('Por favor, completa todos los campos correctamente.');
    }
  });
});