document.addEventListener('DOMContentLoaded', function() {
    // Handler per il pulsante di modifica convocazione
    document.querySelectorAll('.edit-convocazione-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Recupera i dati dalla convocazione
            const convId = this.getAttribute('data-conv-id');
            const dataInizio = this.getAttribute('data-data-inizio');
            const orarioPartenza = this.getAttribute('data-orario-partenza');
            const sport = this.getAttribute('data-sport');
            const categoria = this.getAttribute('data-categoria');
            const tipoGara = this.getAttribute('data-tipo-gara');
            const squadre = this.getAttribute('data-squadre');
            const luogo = this.getAttribute('data-luogo');
            const trasferta = this.getAttribute('data-trasferta');
            const indennizzo = this.getAttribute('data-indennizzo');
            const note = this.getAttribute('data-note');
            
            // Aggiorna il form modale
            const form = document.getElementById('editConvocazioneForm');
            form.action = `/update/${convId}`;
            
            // Popola i campi
            document.getElementById('editDataInizio').value = formatDateTime(dataInizio);
            document.getElementById('editOrarioPartenza').value = orarioPartenza;
            document.getElementById('editTipoGara').value = tipoGara;
            document.getElementById('editSquadre').value = squadre;
            document.getElementById('editLuogo').value = luogo;
            document.getElementById('editTrasferta').value = trasferta;
            document.getElementById('editIndennizzo').value = indennizzo;
            document.getElementById('editNote').value = note;
            
            // Per i campi sport e categoria, dobbiamo gestirli diversamente
            // poiché nel modale usiamo il campo sport_id, ma nella tabella
            // abbiamo il nome dello sport
            const sportSelect = document.getElementById('editSport');
            
            // Cerca l'opzione che corrisponde al nome dello sport
            for (let i = 0; i < sportSelect.options.length; i++) {
                if (sportSelect.options[i].text === sport) {
                    sportSelect.selectedIndex = i;
                    break;
                }
            }
            
            // Aggiorna le categorie associate allo sport
            // Questa parte dovrà essere implementata dopo aver creato la logica
            // per caricare le categorie in base allo sport selezionato
        });
    });
    
    // Funzione per formattare la data in formato datetime-local
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
    
    // Variabile per memorizzare i dati delle categorie
    let categorieData = {};
    
    // Funzione per caricare le categorie in base allo sport selezionato
    function loadCategorieForSport(sportId) {
        const categoriaSelect = document.getElementById('editCategoria');
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        // Se non abbiamo ancora dati delle categorie, li recuperiamo dal server
        if (Object.keys(categorieData).length === 0) {
            fetch('/api/categorie')
                .then(response => response.json())
                .then(data => {
                    categorieData = data;
                    populateCategorie(sportId);
                })
                .catch(error => {
                    console.error('Errore nel recupero delle categorie:', error);
                });
        } else {
            populateCategorie(sportId);
        }
    }
    
    // Funzione per popolare il dropdown delle categorie
    function populateCategorie(sportId) {
        const categoriaSelect = document.getElementById('editCategoria');
        categoriaSelect.innerHTML = '<option value="">Seleziona categoria</option>';
        
        if (!sportId || !categorieData[sportId]) {
            return;
        }
        
        categorieData[sportId].forEach(categoria => {
            const option = document.createElement('option');
            option.value = categoria.id;
            option.textContent = categoria.nome;
            categoriaSelect.appendChild(option);
        });
    }
    
    // Listener per il cambio di sport
    const sportSelect = document.getElementById('editSport');
    if (sportSelect) {
        sportSelect.addEventListener('change', function() {
            loadCategorieForSport(this.value);
        });
    }
    
    // Aggiunge tooltips per contenuti troncati
    document.querySelectorAll('.text-truncate').forEach(element => {
        element.setAttribute('title', element.textContent);
    });
});