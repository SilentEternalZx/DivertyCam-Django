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

// Detectar cambios y guardar configuración
document.getElementById('printerSelect').addEventListener('change', savePrinterSettings);
document.getElementById('paperSize').addEventListener('change', savePrinterSettings);
document.getElementById('orientation').addEventListener('change', savePrinterSettings);

async function savePrinterSettings() {
    const printerName = document.getElementById('printerSelect').value;
    const paperSize = document.getElementById('paperSize').value;
    const orientation = document.getElementById('orientation').value;

    await fetch('/usuarios/save_printer_settings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            printer_name: printerName,
            paper_size: paperSize,
            orientation: orientation
        })
    });
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

document.getElementById('printerSelect').addEventListener('change', async (event) => {
    const printerName = event.target.value;
    if (!printerName) return;

    const response = await fetch('/usuarios/get_paper_sizes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ printer_name: printerName })
    });

    const data = await response.json();

    const paperSizeSelect = document.getElementById('paperSize');
    paperSizeSelect.innerHTML = '';

    if (data.paper_sizes && data.paper_sizes.length > 0) {
        data.paper_sizes.forEach(size => {
            const option = document.createElement('option');
            option.value = size.name;
            option.textContent = size.name;
            paperSizeSelect.appendChild(option);

            // Seleccionar tamaño predeterminado
            if (size.id === data.default) {
                option.selected = true;
            }
        });

        updatePaperPreview();  // Actualiza la previsualización con el nuevo tamaño
    } else {
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No se detectaron tamaños de papel';
        paperSizeSelect.appendChild(option);
    }
});

function updatePaperPreview() {
    const paperSize = document.getElementById('paperSize').value;
    const orientation = document.getElementById('orientation').value;
    const preview = document.getElementById('paperPreview');

    const sizes = {
        A4: { width: 210, height: 297 },
        A3: { width: 297, height: 420 },
        A5: { width: 148, height: 210 },
        Letter: { width: 216, height: 279 },
        Legal: { width: 216, height: 356 },
        Executive: { width: 184, height: 267 },
        Tabloid: { width: 279, height: 432 },
        Statement: { width: 140, height: 216 },
        B4: { width: 250, height: 353 },
        B5: { width: 176, height: 250 },
        Folio: { width: 210, height: 330 },
        Envelope9: { width: 98, height: 225 },
        Envelope10: { width: 105, height: 241 },
    };

    let width = 210, height = 297; // Valor por defecto A4

    if (sizes[paperSize]) {
        width = sizes[paperSize].width;
        height = sizes[paperSize].height;
    }

    if (orientation === 'landscape') {
        [width, height] = [height, width];
    }

    const scale = 0.7; // Escala para mostrar visualmente sin desbordar
    preview.style.width = (width * scale) + 'px';
    preview.style.height = (height * scale) + 'px';
}
