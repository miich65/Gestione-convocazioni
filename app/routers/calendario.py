from fastapi import APIRouter
from fastapi.responses import FileResponse
import sqlite3
from ics import Calendar, Event
from datetime import datetime, timedelta
import os

router = APIRouter()

@router.get("/calendario.ics")
def calendario_ics():
    """Genera un file ICS con tutte le convocazioni"""
    # Assicurati che la directory esista
    os.makedirs("app/data", exist_ok=True)

    # Connessione al database
    conn = sqlite3.connect("app/data/convocazioni.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni")
    rows = cursor.fetchall()
    conn.close()

    # Crea un nuovo calendario
    cal = Calendar()

    # Colonne del database
    # 0:id, 1:data_inizio, 2:orario_partenza, 3:sport, 4:categoria, 
    # 5:tipo_gara, 6:squadre, 7:luogo, 8:trasferta, 9:indennizzo, 10:note
    for row in rows:
        # Converti le date
        try:
            # Combina data e ora di inizio
            data_inizio = datetime.fromisoformat(row[1])
            orario_partenza = datetime.fromisoformat(row[2]) if row[2] else data_inizio

            # Crea un evento
            ev = Event()
            ev.name = f"{row[3]} - {row[4]} ({row[5]})"
            ev.begin = data_inizio
            
            # Imposta la durata dell'evento (2 ore di default)
            ev.duration = timedelta(hours=2)
            
            # Dettagli aggiuntivi
            ev.location = row[7]
            
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
            # Un giorno prima
            ev.alarms = [
                {
                    'action': 'display',
                    'trigger': timedelta(days=-1)
                },
                # 2 ore prima della partenza
                {
                    'action': 'display',
                    'trigger': (orario_partenza - data_inizio)
                }
            ]

            # Aggiungi l'evento al calendario
            cal.events.add(ev)

        except Exception as e:
            # Log dell'errore (in un'applicazione reale, usa logging)
            print(f"Errore nella conversione dell'evento: {e}")

    # Salva il calendario
    calendario_path = "app/data/calendario.ics"
    with open(calendario_path, "w", encoding="utf-8") as f:
        f.writelines(cal.serialize_iter())

    # Restituisci il file
    return FileResponse(
        calendario_path, 
        media_type='text/calendar', 
        filename='calendario_convocazioni.ics'
    )