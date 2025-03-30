document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM completamente caricato e analizzato");
    
    // Riferimenti agli elementi del form
    const sportSelect = document.getElementById('sportSelect');
    const categoriaSelect = document.getElementById('categoriaSelect');
    const indennizzoField = document.getElementById('indennizzoField');
    const convocazioneForm = document.getElementById('convocazioneForm');

    // Ottieni i dati delle categorie dal backend
    let categorieData = {};
    const dataElement = document.getElementById('categorieData');
    
    if (dataElement) {
        try {
            categorieData = JSON.parse(dataElement.textContent);
            console.log("Dati categorie caricati:", categorieData);
        } catch (e) {
            console.error('Errore nel parsing dei dati delle categorie:', e);
        }
    } else {
        console.error('Elemento categorieData non trovato nel DOM');
    }

    // Funzione per popolare il dropdown delle categorie in base allo sport selezionato
    function updateCategorieDropdown() {
        // Pulisci il dropdown delle categorie
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        // Ottieni l'ID dello sport selezionato
        const sportId = sportSelect.value;
        console.log("Sport selezionato ID:", sportId, "Tipo:", typeof sportId);
        
        if (!sportId) {
            // Se nessuno sport è selezionato, disabilita il dropdown delle categorie
            categoriaSelect.disabled = true;
            indennizzoField.value = '';
            console.log("Nessuno sport selezionato, dropdown categorie disabilitato");
            return;
        }
        
        // Cerca le categorie sia come stringa che come numero
        let categorie = categorieData[sportId] || categorieData[String(sportId)] || [];
        console.log("Categorie trovate:", categorie);
        
        if (categorie.length === 0) {
            console.log("Nessuna categoria trovata per lo sport ID:", sportId);
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
        console.log("Dropdown categorie abilitato con", categorie.length, "opzioni");
    }

    // Funzione per aggiornare l'indennizzo in base alla categoria selezionata
    function updateIndennizzo() {
        const selectedOption = categoriaSelect.options[categoriaSelect.selectedIndex];
        
        if (selectedOption && selectedOption.dataset.indennizzo) {
            indennizzoField.value = selectedOption.dataset.indennizzo;
            console.log("Indennizzo impostato a:", selectedOption.dataset.indennizzo);
        } else {
            indennizzoField.value = '';
            console.log("Indennizzo azzerato, nessuna categoria selezionata");
        }
    }

    // Aggiungi i listener degli eventi
    if (sportSelect) {
        console.log("Aggiunto listener change a sportSelect");
        sportSelect.addEventListener('change', function() {
            console.log("Evento change su sportSelect rilevato");
            updateCategorieDropdown();
        });
    } else {
        console.error("Elemento sportSelect non trovato nel DOM");
    }
    
    if (categoriaSelect) {
        console.log("Aggiunto listener change a categoriaSelect");
        categoriaSelect.addEventListener('change', updateIndennizzo);
    } else {
        console.error("Elemento categoriaSelect non trovato nel DOM");
    }

    // Validazione del form
    if (convocazioneForm) {
        convocazioneForm.addEventListener('submit', function(event) {
            if (!convocazioneForm.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                console.log("Form validazione fallita");
                
                // Aggiungi la classe 'was-validated' per mostrare i messaggi di errore di Bootstrap
                convocazioneForm.classList.add('was-validated');
            } else {
                console.log("Form validazione riuscita");
            }
        });
    } else {
        console.error("Elemento convocazioneForm non trovato nel DOM");
    }

    // Inizializza il dropdown delle categorie se uno sport è già selezionato
    if (sportSelect && sportSelect.value) {
        console.log("Sport già selezionato all'avvio, aggiorno categorie");
        updateCategorieDropdown();
    }
    
    // Aggiungi un log per verificare che lo script sia stato caricato
    console.log("Script form-convocazione.js caricato correttamente");
});