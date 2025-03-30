document.addEventListener('DOMContentLoaded', function() {
    // Seleziona tutti i bottoni di modifica convocazione
    const editButtons = document.querySelectorAll('.edit-convocazione-btn');
    const editForm = document.getElementById('editConvocazioneForm');

    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Recupera i dati dalla riga corrente
            const convId = this.dataset.convId;
            const dataInizio = this.dataset.dataInizio;
            const orarioPartenza = this.dataset.orarioPartenza;
            const sport = this.dataset.sport;
            const categoria = this.dataset.categoria;
            const tipoGara = this.dataset.tipoGara;
            const squadre = this.dataset.squadre;
            const luogo = this.dataset.luogo;
            const trasferta = this.dataset.trasferta;
            const indennizzo = this.dataset.indennizzo;
            const note = this.dataset.note;

            // Imposta i valori nel form di modifica
            document.getElementById('editDataInizio').value = dataInizio;
            document.getElementById('editOrarioPartenza').value = orarioPartenza;
            document.getElementById('editSport').value = sport;
            document.getElementById('editCategoria').value = categoria;
            document.getElementById('editTipoGara').value = tipoGara;
            document.getElementById('editSquadre').value = squadre;
            document.getElementById('editLuogo').value = luogo;
            document.getElementById('editTrasferta').value = trasferta;
            document.getElementById('editIndennizzo').value = indennizzo;
            document.getElementById('editNote').value = note;

            // Imposta l'azione del form con l'ID corretto
            editForm.action = `/update/${convId}`;
        });
    });
    // Parse categories from server-side
    const categorieBySport = JSON.parse('{{ categorie_json|tojson|safe }}');
    
    // Select elements
    const sportSelect = document.getElementById("sportSelect");
    const categoriaSelect = document.getElementById("categoriaSelect");
    const indennizzoField = document.getElementById("indennizzoField");
    const form = document.getElementById("convocazioneForm");

    // Funzione per popolare le categorie
    function populateCategories(sportId) {
        // Resetta la select delle categorie
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        // Se sono presenti categorie per questo sport
        if (categorieBySport[sportId]) {
            categorieBySport[sportId].forEach(cat => {
                const option = document.createElement("option");
                option.value = cat.nome;
                option.dataset.indennizzo = cat.indennizzo;
                option.textContent = cat.nome;
                categoriaSelect.appendChild(option);
            });
            
            // Abilita la select
            categoriaSelect.disabled = false;
            categoriaSelect.classList.remove('disabled');
        } else {
            // Disabilita se non ci sono categorie
            categoriaSelect.disabled = true;
        }
    }

    // Listener per la selezione dello sport
    sportSelect.addEventListener("change", () => {
        const sportId = sportSelect.value;
        
        // Resetta l'indennizzo
        indennizzoField.value = "";
        
        // Popola le categorie
        populateCategories(sportId);
    });

    // Listener per la selezione della categoria
    categoriaSelect.addEventListener("change", () => {
        const selectedOption = categoriaSelect.selectedOptions[0];
        if (selectedOption && selectedOption.value !== "") {
            indennizzoField.value = selectedOption.dataset.indennizzo || "";
        }
    });

    // Form validation personalizzata
    form.addEventListener('submit', function(event) {
        // Rimuovi eventuali errori precedenti
        form.querySelectorAll('.was-validated').forEach(el => {
            el.classList.remove('was-validated');
        });

        // Verifica validità
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }

        // Aggiungi classe di validazione
        form.classList.add('was-validated');

        // Controlli personalizzati
        const sportValue = sportSelect.value;
        const categoriaValue = categoriaSelect.value;

        // Se sport è selezionato, assicurati che le categorie siano caricate
        if (sportValue && (!categoriaSelect.options.length || categoriaSelect.disabled)) {
            categoriaSelect.setCustomValidity('Seleziona una categoria per lo sport scelto');
            event.preventDefault();
        } else {
            categoriaSelect.setCustomValidity('');
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