# ---------------------------
# Applicazione FastAPI per gestire convocazioni arbitrali
# ---------------------------

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import sqlite3
import os
from ics import Calendar, Event
from ics.alarm import DisplayAlarm
from datetime import datetime, timedelta


# Inizializzazione dell'app FastAPI
app = FastAPI()

# ---------------------------
# Configurazione del database SQLite
# ---------------------------
DB_PATH = "data/convocazioni.db"
os.makedirs("data", exist_ok=True)  # Crea la cartella data se non esiste

# Creazione della tabella se non esiste
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS convocazioni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_inizio TEXT,
        orario_partenza TEXT,
        sport TEXT,
        squadre TEXT,
        luogo TEXT,
        trasferta INTEGER,
        indennizzo REAL,
        note TEXT
    )
''')
conn.commit()
conn.close()

# ---------------------------
# Configurazione delle statiche e dei template HTML
# ---------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------------------
# Pagina iniziale con il form per inserire la convocazione
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def form_get(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

# ---------------------------
# Pagina con la lista delle convocazioni
# ---------------------------
@app.get("/convocazioni", response_class=HTMLResponse)
def lista_convocazioni(request: Request):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni ORDER BY data_inizio DESC")
    convocazioni = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return templates.TemplateResponse("convocazioni.html", {"request": request, "convocazioni": convocazioni})


# ---------------------------
# Endpoint per gestire l'invio del form e salvare la convocazione nel DB
# ---------------------------
@app.post("/add")
def form_post(
    request: Request,
    data_inizio: str = Form(...),
    orario_partenza: str = Form(...),
    sport: str = Form(...),
    squadre: str = Form(...),
    luogo: str = Form(...),
    trasferta: float = Form(0.0),  # <-- ora è float (CHF)
    indennizzo: float = Form(...),
    note: str = Form("")
):
    # Connessione al DB e inserimento della convocazione
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO convocazioni (data_inizio, orario_partenza, sport, squadre, luogo, trasferta, indennizzo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_inizio,
        orario_partenza,
        sport,
        squadre,
        luogo,
        trasferta,
        indennizzo,
        note
    ))
    conn.commit()
    conn.close()
    return templates.TemplateResponse("form.html", {"request": request, "msg": "Convocazione salvata!"})

# ---------------------------
# Endpoint per eliminare una convocazione
# ---------------------------
from fastapi.responses import RedirectResponse

@app.post("/delete/{conv_id}")
def delete_convocazione(conv_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM convocazioni WHERE id=?", (conv_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/convocazioni", status_code=303)


# ---------------------------
# Endpoint per aggiornare una convocazione
# ---------------------------
@app.post("/update/{conv_id}")
def update_convocazione(
    conv_id: int,
    data_inizio: str = Form(...),
    orario_partenza: str = Form(...),
    sport: str = Form(...),
    squadre: str = Form(...),
    luogo: str = Form(...),
    trasferta: float = Form(0.0),
    indennizzo: float = Form(...),
    note: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE convocazioni
        SET data_inizio=?, orario_partenza=?, sport=?, squadre=?, luogo=?, trasferta=?, indennizzo=?, note=?
        WHERE id=?
    """, (
        data_inizio, orario_partenza, sport, squadre, luogo, trasferta, indennizzo, note, conv_id
    ))
    conn.commit()
    conn.close()
    return RedirectResponse("/convocazioni", status_code=303)


# ---------------------------
# Endpoint per generare un file ICS (calendario Apple compatibile)
# ---------------------------
@app.get("/calendario.ics")
def calendario_ics():
    from dateutil import parser  # aggiungi questa import in cima se vuoi sicurezza

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni")
    rows = cursor.fetchall()
    conn.close()

    cal = Calendar()
    for row in rows:
        data_inizio = datetime.fromisoformat(row[1])
        partenza = datetime.fromisoformat(row[2])

        ev = Event()
        ev.name = row[4]               # squadre
        ev.begin = data_inizio
        ev.end = data_inizio + timedelta(hours=2)
        ev.location = row[5]           # luogo
        ev.description = row[8]        # note

        ev.alarms = [
            DisplayAlarm(trigger=partenza - data_inizio),  # X ore prima della partita (es: -2h)
            DisplayAlarm(trigger=timedelta(days=-1)),      # 1 giorno prima
        ]
        cal.events.add(ev)

    with open("data/calendario.ics", "w") as f:
        f.writelines(cal.serialize_iter())

    return FileResponse("data/calendario.ics", media_type='text/calendar')
