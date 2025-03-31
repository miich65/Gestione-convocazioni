document.addEventListener('DOMContentLoaded', function() {
    // Seleziona tutti i bottoni di modifica convocazione
    const editButtons = document.querySelectorAll('.edit-convocazione-btn');
    const editForm = document.getElementById('editConvocazioneForm');

    editButtons.forEach(button => {
    const categoriePerSport = {};

    // Popola i dati iniziali delle categorie per ogni sport
    function initCategoriePerSport() {
        // Puoi pre-popolare o caricare via AJAX
        fetch('/api/sport-categorie')
            .then(response => response.json())
            .then(data => {
                Object.assign(categoriePerSport, data);
            })
            .catch(error => console.error('Errore nel caricamento delle categorie:', error));
    }
    
    // Inizializza se necessario
    initCategoriePerSport();
    
    // Funzione per aggiornare il dropdown delle categorie in base allo sport selezionato
    function updateCategorieDropdown(sportId, categoriaSelect, selectedCategoriaId = null) {
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        if (!sportId) return;
        
        if (categoriePerSport[sportId]) {
            categoriePerSport[sportId].forEach(categoria => {
                const option = document.createElement('option');
                option.value = categoria.id;
                option.textContent = categoria.nome;
                
                if (selectedCategoriaId && categoria.id == selectedCategoriaId) {
                    option.selected = true;
                }
                
                categoriaSelect.appendChild(option);
            });
        } else {
            console.warn('Nessuna categoria trovata per lo sport ID:', sportId);
        }
    }

    // Gestione modale edit
    const editModal = document.getElementById('editConvocazioneModal');
    if (editModal) {
        editModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const convId = button.getAttribute('data-conv-id');
            const sportValue = button.getAttribute('data-sport');
            const categoriaValue = button.getAttribute('data-categoria');
            
            // Aggiorna il form action
            document.getElementById('editConvocazioneForm').action = `/update/${convId}`;
            
            // Popola i campi
            document.getElementById('editDataInizio').value = button.getAttribute('data-data-inizio');
            document.getElementById('editOrarioPartenza').value = button.getAttribute('data-orario-partenza');
            document.getElementById('editTipoGara').value = button.getAttribute('data-tipo-gara');
            document.getElementById('editSquadre').value = button.getAttribute('data-squadre');
            document.getElementById('editLuogo').value = button.getAttribute('data-luogo');
            document.getElementById('editTrasferta').value = button.getAttribute('data-trasferta');
            document.getElementById('editIndennizzo').value = button.getAttribute('data-indennizzo');
            document.getElementById('editNote').value = button.getAttribute('data-note');
            
            // Trova e seleziona lo sport corretto nel dropdown
            const sportSelect = document.getElementById('editSport');
            const categoriaSelect = document.getElementById('editCategoria');
            
            // Trova lo sport con il nome corrispondente
            Array.from(sportSelect.options).forEach(option => {
                if (option.textContent === sportValue) {
                    option.selected = true;
                    
                    // Aggiorna il dropdown categorie
                    updateCategorieDropdown(option.value, categoriaSelect);
                    
                    // Seleziona la categoria corretta
                    Array.from(categoriaSelect.options).forEach(catOption => {
                        if (catOption.textContent === categoriaValue) {
                            catOption.selected = true;
                        }
                    });
                }
            });
            
            // Aggiungi listener per il cambio di sport
            sportSelect.addEventListener('change', function() {
                updateCategorieDropdown(this.value, categoriaSelect);
            });
        });
    }
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
});