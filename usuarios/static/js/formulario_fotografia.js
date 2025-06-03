document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.getElementById('form');
  const inputDescripcion = document.querySelector('textarea[name="descripcion"]');
  const inputImagen = document.querySelector('input[name="img"]');
  const errorDivDescripcion = document.getElementById('error-descripcion');
  const errorDivImagen = document.getElementById('error-img');
  const maxFileSize = 2 * 1024 * 1024; // 2MB

  // Regex y mensajes
  const expresiones = {
    descripcion: /^[a-zA-ZÀ-ÿ0-9\s]{5,50}$/
  };

  const mensajes = {
    descripcion: "La descripción debe contener entre 5 y 50 caracteres.",
    img: "Debes seleccionar una imagen.",
    img_tipo: "Solo se permiten archivos de imagen.",
  
  };

  // Estado de validación de los campos
  const campos = {
    img: false,
    descripcion: false
  };

  // Validación de la descripción
  function validarDescripcion() {
    const value = inputDescripcion.value.trim();
    if (value === "") {
      errorDivDescripcion.textContent = "Este campo no puede estar vacío.";
      inputDescripcion.classList.add('is-invalid');
      inputDescripcion.classList.remove('is-valid');
      campos.descripcion = false;
      return;
    }
    if (!expresiones.descripcion.test(value)) {
      errorDivDescripcion.textContent = mensajes.descripcion;
      inputDescripcion.classList.add('is-invalid');
      inputDescripcion.classList.remove('is-valid');
      campos.descripcion = false;
      return;
    }
    errorDivDescripcion.textContent = "";
    inputDescripcion.classList.remove('is-invalid');
    inputDescripcion.classList.add('is-valid');
    campos.descripcion = true;
  }

  // Validación de la imagen
  function validarImagen() {
    const files = inputImagen.files;
    if (!files || files.length === 0) {
      errorDivImagen.textContent = mensajes.img;
      inputImagen.classList.add('is-invalid');
      inputImagen.classList.remove('is-valid');
      campos.img = false;
      return;
    }
    const file = files[0];
    if (!file.type.startsWith('image/')) {
      errorDivImagen.textContent = mensajes.img_tipo;
      inputImagen.classList.add('is-invalid');
      inputImagen.classList.remove('is-valid');
      campos.img = false;
      return;
    }
   
    errorDivImagen.textContent = "";
    inputImagen.classList.remove('is-invalid');
    inputImagen.classList.add('is-valid');
    campos.img = true;
  }

  // Eventos individuales
  inputDescripcion.addEventListener('keyup', validarDescripcion);
  inputDescripcion.addEventListener('blur', validarDescripcion);
  inputImagen.addEventListener('change', validarImagen);

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