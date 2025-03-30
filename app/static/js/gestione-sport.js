document.addEventListener('DOMContentLoaded', function() {
    // Variabili elementi DOM
    const filterSport = document.getElementById('filterSport');
    const categorieCards = document.querySelectorAll('.categoria-card');
    const categorieContainer = document.getElementById('categorie-container');
    
    // Funzione per filtrare categorie
    function filterCategories(sportId) {
        let visibleCount = 0;
        categorieCards.forEach(card => {
            const isVisible = sportId === 'all' || card.dataset.sportId === sportId;
            card.classList.toggle('d-none', !isVisible);
            if (isVisible) visibleCount++;
        });
        
        // Gestione messaggio "nessun risultato"
        let noResultsMsg = document.getElementById('no-categories-message');
        if (visibleCount === 0) {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.id = 'no-categories-message';
                noResultsMsg.className = 'col-12 text-center py-4';
                noResultsMsg.innerHTML = '<p class="text-muted">Nessuna categoria trovata per questo sport.</p>';
                categorieContainer.appendChild(noResultsMsg);
            }
        } else if (noResultsMsg) {
            noResultsMsg.remove();
        }
    }
    
    // Listener ed eventi
    filterSport.addEventListener('change', function() {
        filterCategories(this.value);
        localStorage.setItem('selectedSportFilter', this.value);
    });
    
    // Inizializzazione
    const lastSelectedFilter = localStorage.getItem('selectedSportFilter');
    if (lastSelectedFilter) filterSport.value = lastSelectedFilter;
    filterCategories(filterSport.value);
    
    // Animazione card
    document.querySelectorAll('.categoria-item').forEach((card, index) => {
        setTimeout(() => card.style.opacity = '1', index * 50);
    });
    
    // Tooltips per testi troncati
    document.querySelectorAll('.text-truncate').forEach(element => {
        element.setAttribute('title', element.textContent);
    });
    
    // Preparazione form eliminazione
    document.querySelectorAll('form[action^="/delete-categoria/"]').forEach(form => {
        const categoriaId = form.action.split('/').pop();
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'categoria_id';
        hiddenInput.value = categoriaId;
        form.appendChild(hiddenInput);
    });
    
    // Gestione sport selector
    const sportSelector = document.querySelector('select[name="sport_id"]');
    if (sportSelector) {
        sportSelector.addEventListener('change', e => console.log('Sport selezionato:', e.target.value));
    }
    
    // Conferma eliminazione
    document.querySelectorAll('form[action^="/delete-"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const isCategory = form.action.includes('delete-categoria');
            const confirmMessage = isCategory ? 
                'Sei sicuro di voler eliminare questa categoria?' : 
                'Sei sicuro di voler eliminare questo sport? Tutte le categorie associate saranno eliminate.';
            
            if (!confirm(confirmMessage)) e.preventDefault();
        });
    });
    
    // Gestione modali
    const sportModal = document.getElementById('editSportModal');
    if(sportModal) {
        sportModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            document.getElementById('editSportName').value = button.getAttribute('data-sport-name');
            document.getElementById('editSportForm').action = `/update-sport/${button.getAttribute('data-sport-id')}`;
        });
    }
    
    const categoriaModal = document.getElementById('editCategoriaModal');
    if(categoriaModal) {
        categoriaModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            document.getElementById('editCategoriaNome').value = button.getAttribute('data-categoria-nome');
            document.getElementById('editCategoriaSport').value = button.getAttribute('data-categoria-sport');
            document.getElementById('editCategoriaIndennizzo').value = button.getAttribute('data-categoria-indennizzo');
            document.getElementById('editCategoriaForm').action = `/update-categoria/${button.getAttribute('data-categoria-id')}`;
        });
    }
});
