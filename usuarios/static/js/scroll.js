// Mostrar u ocultar el botón según el scroll
    window.onscroll = function() {
        const btn = document.getElementById("btn-scroll-top");
        if (window.scrollY > 250) {
            btn.style.display = "block";
        } else {
            btn.style.display = "none";
        }
    };

    // Hacer scroll suave al top al hacer click
    document.addEventListener("DOMContentLoaded", function() {
        document.getElementById("btn-scroll-top").onclick = function() {
            window.scrollTo({ top: 0, behavior: "smooth" });
        };
    });