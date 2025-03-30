document.addEventListener('DOMContentLoaded', function() {
    // Parse categories from server-side
    const categorieBySport = JSON.parse('{{ categorie_json|tojson|safe }}');
    
    // Select elements
    const sportSelect = document.getElementById("sportSelect");
    const categoriaSelect = document.getElementById("categoriaSelect");
    const indennizzoField = document.getElementById("indennizzoField");

    // Funzione per popolare le categorie
    function populateCategories(sportId) {
        // Resetta la select delle categorie
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        categoriaSelect.disabled = false;
        
        // Se sono presenti categorie per questo sport
        if (categorieBySport[sportId]) {
            categorieBySport[sportId].forEach(cat => {
                const option = document.createElement("option");
                option.value = cat.nome;
                option.dataset.indennizzo = cat.indennizzo;
                option.textContent = cat.nome;
                categoriaSelect.appendChild(option);
            });
        } else {
            // Nessuna categoria disponibile
            const option = document.createElement("option");
            option.value = "";
            option.textContent = "Nessuna categoria disponibile";
            option.disabled = true;
            categoriaSelect.appendChild(option);
            categoriaSelect.disabled = true;
        }
    }

    // Listener per la selezione dello sport
    sportSelect.addEventListener("change", () => {
        const sportId = sportSelect.value;
        
        // Resetta l'indennizzo e la categoria
        indennizzoField.value = "";
        categoriaSelect.value = "";
        
        // Popola le categorie
        if (sportId) {
            populateCategories(sportId);
        } else {
            categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
            categoriaSelect.disabled = true;
        }
    });

    // Listener per la selezione della categoria
    categoriaSelect.addEventListener("change", () => {
        const selectedOption = categoriaSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value !== "") {
            indennizzoField.value = selectedOption.dataset.indennizzo || "";
        }
    });

    // Imposta data di default
    const dataInizioInput = document.getElementById('dataInizio');
    const now = new Date();
    const localDatetime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
        .toISOString().slice(0, 16);
    dataInizioInput.value = localDatetime;

    // Popola le categorie al caricamento se uno sport è già selezionato
    if (sportSelect.value) {
        populateCategories(sportSelect.value);
    }
});