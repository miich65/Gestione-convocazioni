document.addEventListener('DOMContentLoaded', function() {
    // Variabile per memorizzare i dati delle categorie
    let categorieData = {};
    
    // Funzione per recuperare le categorie dal server
    async function fetchCategorieData() {
        try {
            // Endpoint API per ottenere le categorie
            const response = await fetch('/api/categorie');
            if (!response.ok) {
                throw new Error('Errore nel recupero delle categorie');
            }
            const data = await response.json();
            console.log('Dati categorie ricevuti:', data);
            categorieData = data;
            return data;
        } catch (error) {
            console.error('Errore nel recupero delle categorie:', error);
            return {};
        }
    }
    
    // Fetch iniziale delle categorie
    fetchCategorieData();
    
    // Funzione per popolare il dropdown delle categorie basato su uno sport
    function populateCategorieDropdown(sportId) {
        const categoriaSelect = document.getElementById('editCategoria');
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        if (!sportId || !categorieData || !categorieData[sportId]) {
            console.log('Nessuna categoria trovata per sport ID:', sportId);
            categoriaSelect.disabled = true;
            return;
        }
        
        categorieData[sportId].forEach(categoria => {
            const option = document.createElement('option');
            option.value = categoria.id;
            option.textContent = categoria.nome;
            option.dataset.indennizzo = categoria.indennizzo;
            categoriaSelect.appendChild(option);
        });
        
        // Abilita il dropdown delle categorie
        categoriaSelect.disabled = false;
        
        console.log('Dropdown categorie popolato con', categorieData[sportId].length, 'opzioni');
    }
    
    // Handler per il cambio di sport nel modale
    const sportSelect = document.getElementById('editSport');
    if (sportSelect) {
        sportSelect.addEventListener('change', function() {
            const sportId = this.value;
            console.log('Sport selezionato:', sportId);
            
            // Disabilita il dropdown delle categorie se non è selezionato uno sport
            const categoriaSelect = document.getElementById('editCategoria');
            if (!sportId) {
                categoriaSelect.disabled = true;
                categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
                return;
            }
            
            populateCategorieDropdown(sportId);
            
            // Aggiorna anche l'indennizzo se c'è una categoria di default selezionata
            if (categoriaSelect.selectedIndex > 0) {
                updateIndennizzo();
            }
        });
    }
    
    // Funzione per aggiornare l'indennizzo in base alla categoria selezionata
    function updateIndennizzo() {
        const categoriaSelect = document.getElementById('editCategoria');
        const indennizzoField = document.getElementById('editIndennizzo');
        
        if (categoriaSelect.selectedIndex > 0) {
            const selectedOption = categoriaSelect.options[categoriaSelect.selectedIndex];
            indennizzoField.value = selectedOption.dataset.indennizzo || '';
            console.log('Indennizzo aggiornato a:', indennizzoField.value);
        }
    }
    
    // Handler per il cambio di categoria
    const categoriaSelect = document.getElementById('editCategoria');
    if (categoriaSelect) {
        categoriaSelect.addEventListener('change', updateIndennizzo);
    }
    
    // Formatta una data in formato datetime-local
    function formatDateTime(dateTimeStr) {
        try {
            const dt = new Date(dateTimeStr);
            
            const year = dt.getFullYear();
            const month = (dt.getMonth() + 1).toString().padStart(2, '0');
            const day = dt.getDate().toString().padStart(2, '0');
            const hours = dt.getHours().toString().padStart(2, '0');
            const minutes = dt.getMinutes().toString().padStart(2, '0');
            
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        } catch (e) {
            console.error('Errore nella formattazione della data:', e);
            return '';
        }
    }
    
    // Handler per il pulsante di modifica convocazione
    document.querySelectorAll('.edit-convocazione-btn').forEach(button => {
        button.addEventListener('click', async function() {
            // Recupera i dati dalla convocazione
            const convId = this.getAttribute('data-conv-id');
            const dataInizio = this.getAttribute('data-data-inizio');
            const orarioPartenza = this.getAttribute('data-orario-partenza');
            const sport = this.getAttribute('data-sport');
            const sportId = this.getAttribute('data-sport-id');
            const categoria = this.getAttribute('data-categoria');
            const categoriaId = this.getAttribute('data-categoria-id');
            const tipoGara = this.getAttribute('data-tipo-gara');
            const squadre = this.getAttribute('data-squadre');
            const luogo = this.getAttribute('data-luogo');
            const trasferta = this.getAttribute('data-trasferta');
            const indennizzo = this.getAttribute('data-indennizzo');
            const note = this.getAttribute('data-note');
            
            console.log('Modifica convocazione:', {
                convId, sport, sportId, categoria, categoriaId, tipoGara
            });
            
            // Aggiorna il form modale
            const form = document.getElementById('editConvocazioneForm');
            form.action = `/update/${convId}`;
            
            // Popola i campi base
            document.getElementById('editDataInizio').value = formatDateTime(dataInizio);
            document.getElementById('editOrarioPartenza').value = orarioPartenza;
            document.getElementById('editTipoGara').value = tipoGara;
            document.getElementById('editSquadre').value = squadre;
            document.getElementById('editLuogo').value = luogo;
            document.getElementById('editTrasferta').value = trasferta;
            document.getElementById('editIndennizzo').value = indennizzo;
            document.getElementById('editNote').value = note;
            
            // Assicurati che i dati delle categorie siano caricati
            if (Object.keys(categorieData).length === 0) {
                categorieData = await fetchCategorieData();
            }
            
            // Per sport e categoria, dobbiamo trovare gli ID corrispondenti
            try {
                // Recupera gli sport
                const sportResponse = await fetch('/api/sport');
                const sportData = await sportResponse.json();
                
                // Trova l'ID dello sport basato sul nome (se non è già disponibile)
                let selectedSportId = sportId || '';
                if (!selectedSportId && sport) {
                    for (const s of sportData) {
                        if (s.nome === sport) {
                            selectedSportId = s.id.toString();
                            break;
                        }
                    }
                }
                
                // Imposta lo sport nel dropdown
                if (selectedSportId) {
                    const sportSelect = document.getElementById('editSport');
                    sportSelect.value = selectedSportId;
                    
                    // Popola il dropdown delle categorie
                    populateCategorieDropdown(selectedSportId);
                    
                    // Trova la categoria basata sul nome o ID
                    let selectedCategoriaId = categoriaId || '';
                    if (!selectedCategoriaId && categoria && categorieData[selectedSportId]) {
                        for (const cat of categorieData[selectedSportId]) {
                            if (cat.nome === categoria) {
                                selectedCategoriaId = cat.id.toString();
                                break;
                            }
                        }
                    }
                    
                    // Imposta la categoria nel dropdown (con un piccolo ritardo per essere sicuri che il dropdown sia popolato)
                    if (selectedCategoriaId) {
                        setTimeout(() => {
                            const categoriaSelect = document.getElementById('editCategoria');
                            categoriaSelect.value = selectedCategoriaId;
                            updateIndennizzo();
                        }, 100);
                    }
                }
            } catch (error) {
                console.error('Errore nel recupero dei dati dello sport e categoria:', error);
            }
        });
    });
    
    // Conferma eliminazione
    document.querySelectorAll('form[action^="/delete/"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Sei sicuro di voler eliminare questa convocazione?')) {
                e.preventDefault();
            }
        });
    });
    
    // Aggiunge tooltips per contenuti troncati
    document.querySelectorAll('.text-truncate').forEach(element => {
        element.setAttribute('title', element.textContent);
    });
});