document.addEventListener('DOMContentLoaded', function() {
  const formulario = document.getElementById('form');
  const inputs = document.querySelectorAll('#form input, #form select, #form textarea');
  const checkboxesServicios = document.querySelectorAll('input[name="servicios"]'); // Ajusta el name si es distinto

  const expresiones = {
    nombre: /^[a-zA-ZÀ-ÿ0-9\s]{7,100}$/,
    direccion: /^[a-zA-ZÀ-ÿ0-9\s]{7,50}$/

  };

  const mensajes = {
    nombre: "El nombre debe tener al menos 7 caracteres.",
    direccion: "La dirección debe tener al menos 7 caracteres.",
    fecha_hora: "La fecha y hora tiene que ser superior a la actual.",
    servicios: "Selecciona al menos un servicio.",
  };

  const campos = {
    nombre: false,
    categoria: false,
    fecha_hora: false,
    cliente: false,
    direccion: false,
    servicios: false,
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

    // Validación de fecha_hora (NO mayor a la actual)
    if (field === "fecha_hora") {
      const fechaIngresada = new Date(value);
      const ahora = new Date();
      if (fechaIngresada <= ahora) {
        errorDiv.textContent = mensajes.fecha_hora;
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        campos.fecha_hora = false;
        return;
      }
    }

    // Si pasa todas las validaciones
    errorDiv.textContent = "";
    e.target.classList.remove('is-invalid');
    e.target.classList.add('is-valid');
    campos[field] = true;
  }

  // Validación para los checkboxes de "servicios"
  function validarServicios() {
    const errorDiv = document.getElementById('error-servicios');
    const checked = Array.from(checkboxesServicios).some(cb => cb.checked);
    if (!checked) {
      errorDiv.textContent = mensajes.servicios;
      checkboxesServicios.forEach(cb => cb.classList.add('is-invalid'));
      campos.servicios = false;
    } else {
      errorDiv.textContent = "";
      checkboxesServicios.forEach(cb => cb.classList.remove('is-invalid'));
      campos.servicios = true;
    }
  }

  // Asignar eventos
  inputs.forEach((input) => {
    if (input.type === "checkbox") return; // Los checkboxes "servicios" se validan aparte
    input.addEventListener('keyup', validarFormulario);
    input.addEventListener('blur', validarFormulario);
    input.addEventListener('change', validarFormulario);
  });
  
  if (checkboxesServicios.length) {
    checkboxesServicios.forEach(cb => {
      cb.addEventListener('change', validarServicios);
    });
  }

  // Validación al enviar
  formulario.addEventListener('submit', function(e) {
    // Validar todos los campos input/select/textarea
    inputs.forEach(input => {
      if (input.type !== "checkbox") {
        input.dispatchEvent(new Event('blur'));
      }
    });
    // Validar checkboxes
    validarServicios();

    if (Object.values(campos).includes(false)) {
      e.preventDefault();
      alert('Por favor, completa todos los campos correctamente.');
    }
  });
});