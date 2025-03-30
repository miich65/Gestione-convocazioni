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

def setup_template_filters(templates):
    """Registra i filtri personalizzati per Jinja2"""
    templates.env.filters['datetimeformat'] = datetimeformat