from datetime import datetime

def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    """Formatta le date in modo leggibile"""
    if not value:
        return 'N/A'
    try:
        # Se è una stringa, prova a convertirla
        return datetime.fromisoformat(value).strftime(format)
    except Exception:
        return str(value)

# Aggiungi questo quando configuri i template
templates = Jinja2Templates(directory="app/templates")
templates.env.filters['datetimeformat'] = datetimeformat