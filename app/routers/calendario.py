from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
import sqlite3
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import datetime, timedelta, date
import os
from zoneinfo import ZoneInfo  # Per la gestione dei fusi orari

# Definisci il router
router = APIRouter()

# Percorso del database
DB_PATH = "data/convocazioni.db"
CALENDARIO_PATH = "static/calendario.ics"

# Aggiungi questa costante dopo il percorso del database
LOCAL_TIMEZONE = ZoneInfo("Europe/Zurich")  # Oppure "Europe/Rome" per l'Italia

def generate_ics_file():
    """
    Genera il file ICS e lo salva come file statico.
    Questa funzione può essere chiamata dopo ogni modifica alle convocazioni.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Per accedere alle colonne per nome
    cursor = conn.cursor()
    
    # Query con JOIN per ottenere i nomi di sport e categorie
    cursor.execute("""
        SELECT c.*, 
               COALESCE(s.nome, c.sport) as sport_nome,
               COALESCE(cat.nome, c.categoria) as categoria_nome
        FROM convocazioni c
        LEFT JOIN sport s ON c.sport = s.id OR c.sport = s.nome
        LEFT JOIN categorie cat ON (c.categoria = cat.id OR c.categoria = cat.nome)
                                 AND (s.id = cat.sport_id OR c.sport = s.nome)
        ORDER BY c.data_inizio
    """)
    
    rows = cursor.fetchall()
    conn.close()

    cal = Calendar()
    for row in rows:
        try:
            # Gestione corretta di data_inizio (datetime completo)
            data_inizio = parse_datetime(row['data_inizio'])
            print(data_inizio)
            
            # L'orario di partenza per il promemoria
            orario_partenza = parse_time(row['orario_partenza'], base_date=data_inizio.date())
            
            # Verifica che abbiamo lo sport_nome e categoria_nome
            sport_nome = row['sport_nome'] or row['sport']
            categoria_nome = row['categoria_nome'] or row['categoria']
            
            # Crea un nuovo evento
            ev = Event()
            
            # Titolo con sport, categoria, squadre e tipo gara
            # Formato: "Hockey - Senior: Team A vs Team B (Regular season)"
            ev.name = f"{sport_nome} - {categoria_nome}: {row['squadre']} ({row['tipo_gara']})"
            
            # Data e ora corrette
            ev.begin = data_inizio  # Usa l'orario esatto dell'inizio partita
            ev.end = data_inizio + timedelta(hours=2)  # Durata di 2 ore
            
            # Aggiungi il luogo
            ev.location = row['luogo']
            
            # Descrizione dettagliata
            # Aggiungi informazioni sulla trasferta e le note specificate
            desc_parts = []
            
            if row['trasferta']:
                desc_parts.append(f"Trasferta: CHF {row['trasferta']}")
            
            if row['indennizzo']:
                desc_parts.append(f"Indennizzo: CHF {row['indennizzo']}")
                
            if row['note']:
                desc_parts.append(f"\nNote aggiuntive: \n{row['note']}")
            
            ev.description = "\n".join(desc_parts)

            # Aggiungi i promemoria (allarmi)
            alarms = []

            # 1. Promemoria 1 giorno prima dell'inizio partita
            alarms.append(DisplayAlarm(trigger=timedelta(days=-1)))

            # 2. Promemoria basato sull'orario di partenza (se disponibile)
            if orario_partenza:
                # Assicurati che orario_partenza abbia lo stesso fuso orario di data_inizio
                if orario_partenza.tzinfo != data_inizio.tzinfo:
                    orario_partenza = orario_partenza.replace(tzinfo=data_inizio.tzinfo)
                    
                # Calcola la differenza tra l'orario di partenza e l'inizio partita
                if orario_partenza < data_inizio:
                    # L'orario di partenza è prima dell'inizio partita
                    delta = orario_partenza - timedelta(hours=1) - data_inizio
                    alarms.append(DisplayAlarm(trigger=delta))

            ev.alarms = alarms
            
            # Aggiungi l'evento al calendario
            cal.events.add(ev)
            print(f"Evento aggiunto: {ev.name} il {data_inizio}")
        except Exception as e:
            # In caso di errore, salta l'evento ma continua con gli altri
            print(f"Errore nella creazione dell'evento: {e}, dati: data_inizio={row['data_inizio']}, orario_partenza={row['orario_partenza']}")

    # Assicurati che la directory esista
    os.makedirs(os.path.dirname(CALENDARIO_PATH), exist_ok=True)
    
    with open(CALENDARIO_PATH, "w") as f:
        f.writelines(cal.serialize_iter())

    print(f"File calendario ICS generato in {CALENDARIO_PATH}")
    
def parse_datetime(dt_str):
    """
    Analizza una stringa datetime in un oggetto datetime.
    Gestisce diversi formati possibili e imposta il fuso orario corretto.
    """
    if not dt_str:
        return datetime.now(LOCAL_TIMEZONE)
        
    try:
        # Formato standard ISO
        dt = datetime.fromisoformat(dt_str)
        # Se non ha fuso orario, assegna quello locale
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TIMEZONE)
        return dt
    except ValueError:
        try:
            # Formato data ora comune
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=LOCAL_TIMEZONE)
        except ValueError:
            try:
                # Formato solo data
                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                return dt.replace(tzinfo=LOCAL_TIMEZONE)
            except ValueError:
                # Fallback
                print(f"Impossibile analizzare la data: {dt_str}")
                return datetime.now(LOCAL_TIMEZONE)
            
def parse_time(time_str, base_date=None):
    """
    Analizza una stringa orario in un oggetto datetime.
    Utilizza la data base fornita o oggi come data di base.
    Imposta il fuso orario corretto.
    """
    if not time_str:
        return None
        
    if not base_date:
        base_date = date.today()
        
    try:
        # Prova formato orario standard HH:MM
        hours, minutes = time_str.split(':')
        dt = datetime.combine(
            base_date, 
            datetime.strptime(f"{hours.zfill(2)}:{minutes.zfill(2)}", "%H:%M").time()
        )
        return dt.replace(tzinfo=LOCAL_TIMEZONE)
    except ValueError:
        try:
            # Prova formato orario completo HH:MM:SS
            dt = datetime.combine(
                base_date,
                datetime.strptime(time_str, "%H:%M:%S").time()
            )
            return dt.replace(tzinfo=LOCAL_TIMEZONE)
        except ValueError:
            try:
                # Prova come datetime completo
                dt = datetime.fromisoformat(time_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=LOCAL_TIMEZONE)
                return dt
            except ValueError:
                print(f"Impossibile analizzare l'orario: {time_str}")
                return None

@router.get("/calendario")
def view_calendario(background_tasks: BackgroundTasks):
    """
    Visualizza il calendario e aggiorna il file ICS in background.
    """
    # Genera il calendario ora per assicurarsi che sia aggiornato
    generate_ics_file()
    
    # Reindirizza al file statico
    return RedirectResponse(url="/static/calendario.ics")


# Funzione helper da chiamare dopo ogni modifica alle convocazioni
def update_calendar_after_change():
    """
    Aggiorna il file ICS dopo ogni modifica alle convocazioni.
    Questa funzione può essere importata e chiamata dai router di convocazioni.
    """
    generate_ics_file()