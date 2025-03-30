document.addEventListener('DOMContentLoaded', function() {
    // Parse categories from server-side
    const categorieBySport = JSON.parse('{{ categorie_json|tojson|safe }}');
    
    // Select elements
    const sportSelect = document.getElementById("sportSelect");
    const categoriaSelect = document.getElementById("categoriaSelect");
    const indennizzoField = document.getElementById("indennizzoField");
    const form = document.getElementById("convocazioneForm");

    // Populate categories based on selected sport
    sportSelect.addEventListener("change", () => {
        const sportId = sportSelect.value;
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        categoriaSelect.disabled = true;
        indennizzoField.value = "";
    
        if (categorieBySport[sportId]) {
            categorieBySport[sportId].forEach(cat => {
                const option = document.createElement("option");
                option.value = cat.nome;  // Usa il nome della categoria
                option.dataset.indennizzo = cat.indennizzo;
                option.textContent = cat.nome;
                categoriaSelect.appendChild(option);
            });
            
            categoriaSelect.disabled = false;
        }
    });
    
    categoriaSelect.addEventListener("change", () => {
        const selectedOption = categoriaSelect.selectedOptions[0];
        if (selectedOption) {
            indennizzoField.value = selectedOption.dataset.indennizzo || "";
        }
    });

    // Form validation
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    }, false);

    // Set default date to today
    const dataInizioInput = document.getElementById('dataInizio');
    const now = new Date();
    const localDatetime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString().slice(0, 16);
    dataInizioInput.value = localDatetime;
});