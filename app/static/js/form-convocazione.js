document.addEventListener('DOMContentLoaded', function() {
    // Riferimenti agli elementi del form
    const sportSelect = document.getElementById('sportSelect');
    const categoriaSelect = document.getElementById('categoriaSelect');
    const indennizzoField = document.getElementById('indennizzoField');
    const convocazioneForm = document.getElementById('convocazioneForm');

    // Ottieni i dati delle categorie dal backend
    // Cerca se abbiamo un elemento con id 'categorieData' che contiene i dati delle categorie
    let categorieData = {};
    const dataElement = document.getElementById('categorieData');
    
    if (dataElement) {
        try {
            categorieData = JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('Errore nel parsing dei dati delle categorie:', e);
        }
    }

    // Funzione per popolare il dropdown delle categorie in base allo sport selezionato
    function updateCategorieDropdown() {
        // Pulisci il dropdown delle categorie
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        // Ottieni l'ID dello sport selezionato
        const sportId = sportSelect.value;
        
        if (!sportId) {
            // Se nessuno sport è selezionato, disabilita il dropdown delle categorie
            categoriaSelect.disabled = true;
            indennizzoField.value = '';
            return;
        }
        
        // Ottieni le categorie per lo sport selezionato
        const categorie = categorieData[sportId] || [];
        
        if (categorie.length === 0) {
            categoriaSelect.disabled = true;
            return;
        }
        
        // Popola il dropdown delle categorie
        categorie.forEach(categoria => {
            const option = document.createElement('option');
            option.value = categoria.nome;
            option.textContent = categoria.nome;
            option.dataset.indennizzo = categoria.indennizzo;
            categoriaSelect.appendChild(option);
        });
        
        // Abilita il dropdown delle categorie
        categoriaSelect.disabled = false;
    }

    // Funzione per aggiornare l'indennizzo in base alla categoria selezionata
    function updateIndennizzo() {
        const selectedOption = categoriaSelect.options[categoriaSelect.selectedIndex];
        
        if (selectedOption && selectedOption.dataset.indennizzo) {
            indennizzoField.value = selectedOption.dataset.indennizzo;
        } else {
            indennizzoField.value = '';
        }
    }

    // Aggiungi i listener degli eventi
    sportSelect.addEventListener('change', updateCategorieDropdown);
    categoriaSelect.addEventListener('change', updateIndennizzo);

    // Validazione del form
    convocazioneForm.addEventListener('submit', function(event) {
        if (!convocazioneForm.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            
            // Aggiungi la classe 'was-validated' per mostrare i messaggi di errore di Bootstrap
            convocazioneForm.classList.add('was-validated');
        }
    });

    // Inizializza il dropdown delle categorie se uno sport è già selezionato
    if (sportSelect.value) {
        updateCategorieDropdown();
    }
});