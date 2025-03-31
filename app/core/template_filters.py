from datetime import datetime

def setup_template_filters(templates):
    """Configura i filtri personalizzati per i template Jinja2."""
    
    @templates.env.filter
    def datetimeformat(value, format='%d/%m/%Y %H:%M'):
        """Formatta un oggetto datetime o una stringa datetime."""
        if value is None:
            return ""
            
        if isinstance(value, str):
            try:
                # Prova a convertire una stringa in datetime
                value = datetime.fromisoformat(value)
            except ValueError:
                try:
                    # Formato alternativo
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    # Se non è possibile convertire, restituisci la stringa originale
                    return value
        
        return value.strftime(format)
        
    @templates.env.filter
    def tojson(value):
        """Converte un valore in JSON. Necessario per i dati delle categorie."""
        import json
        return json.dumps(value)