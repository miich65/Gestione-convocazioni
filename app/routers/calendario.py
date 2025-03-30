from fastapi import APIRouter
from fastapi.responses import FileResponse
import sqlite3
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import datetime, timedelta
import os

# Definisci il router
router = APIRouter()

# Percorso del database
DB_PATH = "data/convocazioni.db"

@router.get("/calendario.ics")
def calendario_ics():
    """Genera un file ICS (calendario Apple/Google compatibile) con tutte le convocazioni"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni")
    rows = cursor.fetchall()
    conn.close()

    cal = Calendar()
    for row in rows:
        try:
            data_inizio = datetime.fromisoformat(row[1])
            partenza = datetime.fromisoformat(row[2])

            ev = Event()
            ev.name = f"{row[3]} - {row[4]} ({row[5]})"               
            ev.begin = data_inizio
            ev.end = data_inizio + timedelta(hours=2)
            ev.location = row[7]  # luogo
            
            # Descrizione dettagliata
            ev.description = f"""
            Sport: {row[3]}
            Categoria: {row[4]}
            Tipo Gara: {row[5]}
            Squadre: {row[6]}
            Indennizzo: CHF {row[9]}
            Trasferta: {row[8]} km
            Note: {row[10] or 'Nessuna nota'}
            """

            # Aggiungi promemoria
            ev.alarms = [
                DisplayAlarm(trigger=partenza - data_inizio),  # X ore prima della partita
                DisplayAlarm(trigger=timedelta(days=-1)),      # 1 giorno prima
            ]
            cal.events.add(ev)
        except Exception as e:
            # In caso di errore, salta l'evento ma continua con gli altri
            print(f"Errore nella creazione dell'evento: {e}")

    # Assicurati che la directory esista
    os.makedirs("static", exist_ok=True)
    
    calendario_path = "static/calendario.ics"
    with open(calendario_path, "w") as f:
        f.writelines(cal.serialize_iter())

    return FileResponse(calendario_path, media_type='text/calendar')