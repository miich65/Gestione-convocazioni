from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
import sqlite3
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import datetime, timedelta, date
import os

# Definisci il router
router = APIRouter()

# Percorso del database
DB_PATH = "data/convocazioni.db"
CALENDARIO_PATH = "static/calendario.ics"

def generate_ics_file():
    """
    Genera il file ICS e lo salva come file statico.
    Questa funzione può essere chiamata dopo ogni modifica alle convocazioni.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Per accedere alle colonne per nome
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni")
    rows = cursor.fetchall()
    conn.close()

    cal = Calendar()
    for row in rows:
        try:
            # Gestione corretta di data_inizio (datetime completo)
            data_inizio = parse_datetime(row['data_inizio'])
            
            # Converti l'orario di partenza in un datetime
            orario_partenza = parse_time(row['orario_partenza'], base_date=data_inizio.date())
            
            # Calcola l'anticipo per il promemoria
            if orario_partenza and data_inizio:
                alarm_trigger = orario_partenza - data_inizio
            else:
                alarm_trigger = timedelta(hours=-1)  # Default se non calcolabile
            
            ev = Event()
            ev.name = f"{row['sport']} - {row['categoria']} ({row['tipo_gara']})"               
            ev.begin = data_inizio
            ev.end = data_inizio + timedelta(hours=2)
            ev.location = row['luogo']
            
            # Descrizione dettagliata
            ev.description = f"""
            Note: {row['note'] or 'Nessuna nota'}
            """

            # Aggiungi promemoria
            ev.alarms = [
                DisplayAlarm(trigger=alarm_trigger),  # Ore prima della partita
                DisplayAlarm(trigger=timedelta(days=-1)),  # 1 giorno prima
            ]
            cal.events.add(ev)
            print(f"Evento aggiunto: {row['sport']} - {row['categoria']} il {data_inizio}")
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
    Gestisce diversi formati possibili.
    """
    if not dt_str:
        return datetime.now()
        
    try:
        # Formato standard ISO
        return datetime.fromisoformat(dt_str)
    except ValueError:
        try:
            # Formato data ora comune
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Formato solo data
                return datetime.strptime(dt_str, "%Y-%m-%d")
            except ValueError:
                # Fallback
                print(f"Impossibile analizzare la data: {dt_str}")
                return datetime.now()

def parse_time(time_str, base_date=None):
    """
    Analizza una stringa orario in un oggetto datetime.
    Utilizza la data base fornita o oggi come data di base.
    """
    if not time_str:
        return None
        
    if not base_date:
        base_date = date.today()
        
    try:
        # Prova formato orario standard HH:MM
        hours, minutes = time_str.split(':')
        return datetime.combine(
            base_date, 
            datetime.strptime(f"{hours.zfill(2)}:{minutes.zfill(2)}", "%H:%M").time()
        )
    except ValueError:
        try:
            # Prova formato orario completo HH:MM:SS
            return datetime.combine(
                base_date,
                datetime.strptime(time_str, "%H:%M:%S").time()
            )
        except ValueError:
            try:
                # Prova come datetime completo
                return datetime.fromisoformat(time_str)
            except ValueError:
                print(f"Impossibile analizzare l'orario: {time_str}")
                return None

@router.get("/calendario")
def view_calendario(background_tasks: BackgroundTasks):
    """
    Visualizza il calendario e aggiorna il file ICS in background.
    """
    # Aggiorna il calendario in background
    background_tasks.add_task(generate_ics_file)
    
    # Reindirizza al file statico
    return RedirectResponse(url="/static/calendario.ics")

@router.get("/calendario.ics")
def download_calendario(background_tasks: BackgroundTasks):
    """
    Scarica il file ICS e aggiorna il calendario in background.
    """
    # Aggiorna il calendario in background
    background_tasks.add_task(generate_ics_file)
    
    # Se il file non esiste ancora, crealo prima
    if not os.path.exists(CALENDARIO_PATH):
        generate_ics_file()
    
    return FileResponse(
        CALENDARIO_PATH, 
        media_type='text/calendar',
        filename="calendario_arbitri.ics"
    )

# Funzione helper da chiamare dopo ogni modifica alle convocazioni
def update_calendar_after_change():
    """
    Aggiorna il file ICS dopo ogni modifica alle convocazioni.
    Questa funzione può essere importata e chiamata dai router di convocazioni.
    """
    generate_ics_file()