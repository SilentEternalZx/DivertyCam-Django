document.addEventListener("DOMContentLoaded", () => {
    loadPrinters();
    document.getElementById('paperSize').addEventListener('change', updatePaperPreview);
    document.getElementById('orientation').addEventListener('change', updatePaperPreview);
    updatePaperPreview();
});

async function loadPrinters() {
    const response = await fetch('/usuarios/list_printers/');
    const data = await response.json();
    const select = document.getElementById('printerSelect');

    if (!select) return; // Verificación extra

    select.innerHTML = '';

    if (data.printers.length === 0) {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No hay impresoras disponibles';
        select.appendChild(option);
    } else {
        data.printers.forEach(printer => {
            const option = document.createElement('option');
            option.value = printer;
            option.textContent = printer;
            select.appendChild(option);
        });
    }
}

function updatePaperPreview() {
    const paperSize = document.getElementById('paperSize').value;
    const orientation = document.getElementById('orientation').value;
    const preview = document.getElementById('paperPreview');

    const sizes = {
        A4: { width: 210, height: 297 },
        Letter: { width: 216, height: 279 }
    };

    let width = sizes[paperSize].width;
    let height = sizes[paperSize].height;

    if (orientation === 'landscape') {
        [width, height] = [height, width];
    }

    const scale = 1.2;
    preview.style.width = (width * scale) + 'px';
    preview.style.height = (height * scale) + 'px';
}

async function printDocument() {
    const printerName = document.getElementById('printerSelect').value;
    const documentContent = "Hola desde Django";  // Aquí va el contenido del documento que deseas imprimir
    const paperSize = document.getElementById('paperSize').value;

    const response = await fetch('/usuarios/print_document/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            printer_name: printerName,
            document_content: documentContent,
            paper_size: paperSize
        })
    });

    const result = await response.json();

    if (response.ok) {
        alert(result.message);
    } else {
        alert("❌ Error: " + (result.error || "No se pudo imprimir"));
    }
}
