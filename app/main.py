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
    trasferta: str = Form(...),
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
        1 if trasferta == "on" else 0,
        indennizzo,
        note
    ))
    conn.commit()
    conn.close()
    return templates.TemplateResponse("form.html", {"request": request, "msg": "Convocazione salvata!"})

# ---------------------------
# Endpoint per generare un file ICS (calendario Apple compatibile)
# ---------------------------
@app.get("/calendario.ics")
def calendario_ics():
    # Recupera le convocazioni dal DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni")
    rows = cursor.fetchall()
    conn.close()

    # Crea il calendario ICS
    cal = Calendar()
    for row in rows:
        ev = Event()
        ev.name = row[4]  # squadre
        ev.begin = row[1]  # data_inizio
        ev.location = row[5]  # luogo
        ev.description = row[8]  # note (es. password inline)
        cal.events.add(ev)

    # Scrive il file ICS su disco e lo restituisce come risposta
    with open("data/calendario.ics", "w") as f:
        f.writelines(cal.serialize_iter())

    return FileResponse("data/calendario.ics", media_type='text/calendar')
