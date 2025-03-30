document.addEventListener('DOMContentLoaded', function() {
    // Seleziona tutti i bottoni di modifica convocazione
    const editButtons = document.querySelectorAll('.edit-convocazione-btn');
    const editForm = document.getElementById('editConvocazioneForm');

    // Debug: Verifica se gli elementi esistono
    console.log('Edit Buttons:', editButtons);
    console.log('Edit Form:', editForm);

    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Debug: Stampa tutti i dataset
            console.log('Button Dataset:', this.dataset);

            // Recupera i dati dalla riga corrente
            const convId = this.getAttribute('data-conv-id');
            const dataInizio = this.getAttribute('data-data-inizio');
            const orarioPartenza = this.getAttribute('data-orario-partenza');
            const sport = this.getAttribute('data-sport');
            const categoria = this.getAttribute('data-categoria');
            const tipoGara = this.getAttribute('data-tipo-gara');
            const squadre = this.getAttribute('data-squadre');
            const luogo = this.getAttribute('data-luogo');
            const trasferta = this.getAttribute('data-trasferta') || '0';
            const indennizzo = this.getAttribute('data-indennizzo');
            const note = this.getAttribute('data-note') || '';

            // Debug: Stampa i valori estratti
            console.log('Valori estratti:', {
                convId, dataInizio, orarioPartenza, sport, categoria, 
                tipoGara, squadre, luogo, trasferta, indennizzo, note
            });

            // Seleziona gli elementi del form
            const editDataInizio = document.getElementById('editDataInizio');
            const editOrarioPartenza = document.getElementById('editOrarioPartenza');
            const editSport = document.getElementById('editSport');
            const editCategoria = document.getElementById('editCategoria');
            const editTipoGara = document.getElementById('editTipoGara');
            const editSquadre = document.getElementById('editSquadre');
            const editLuogo = document.getElementById('editLuogo');
            const editTrasferta = document.getElementById('editTrasferta');
            const editIndennizzo = document.getElementById('editIndennizzo');
            const editNote = document.getElementById('editNote');

            // Debug: Verifica l'esistenza degli elementi
            console.log('Elementi form:', {
                editDataInizio, editOrarioPartenza, editSport, editCategoria, 
                editTipoGara, editSquadre, editLuogo, editTrasferta, 
                editIndennizzo, editNote
            });

            // Imposta i valori nel form di modifica
            if (editDataInizio) editDataInizio.value = dataInizio;
            if (editOrarioPartenza) editOrarioPartenza.value = orarioPartenza;
            if (editSport) editSport.value = sport;
            if (editCategoria) editCategoria.value = categoria;
            if (editTipoGara) editTipoGara.value = tipoGara;
            if (editSquadre) editSquadre.value = squadre;
            if (editLuogo) editLuogo.value = luogo;
            if (editTrasferta) editTrasferta.value = trasferta;
            if (editIndennizzo) editIndennizzo.value = indennizzo;
            if (editNote) editNote.value = note;

            // Imposta l'azione del form con l'ID corretto
            if (editForm) {
                editForm.action = `/update/${convId}`;
                console.log('Form action impostata:', editForm.action);
            }
        });
    });

    // Resto del codice precedente...
});