from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
import sqlite3
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import datetime, timedelta
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
            data_inizio = datetime.fromisoformat(row['data_inizio'])
            partenza = datetime.fromisoformat(row['orario_partenza'])

            ev = Event()
            ev.name = f"{row['sport']} - {row['categoria']} ({row['tipo_gara']})"               
            ev.begin = data_inizio
            ev.end = data_inizio + timedelta(hours=2)
            ev.location = row['luogo']
            
            # Descrizione dettagliata
            ev.description = f"""
            Sport: {row['sport']}
            Categoria: {row['categoria']}
            Tipo Gara: {row['tipo_gara']}
            Squadre: {row['squadre']}
            Indennizzo: CHF {row['indennizzo']}
            Trasferta: {row['trasferta']} CHF
            Note: {row['note'] or 'Nessuna nota'}
            """

            # Aggiungi promemoria
            ev.alarms = [
                DisplayAlarm(trigger=partenza - data_inizio),  # Ore prima della partita
                DisplayAlarm(trigger=timedelta(days=-1)),      # 1 giorno prima
            ]
            cal.events.add(ev)
        except Exception as e:
            # In caso di errore, salta l'evento ma continua con gli altri
            print(f"Errore nella creazione dell'evento: {e}")

    # Assicurati che la directory esista
    os.makedirs(os.path.dirname(CALENDARIO_PATH), exist_ok=True)
    
    with open(CALENDARIO_PATH, "w") as f:
        f.writelines(cal.serialize_iter())

    print(f"File calendario ICS generato in {CALENDARIO_PATH}")

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