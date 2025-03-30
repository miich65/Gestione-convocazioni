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
});