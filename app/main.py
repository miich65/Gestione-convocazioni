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

# ---------------------------
# Connessione al database e creazione delle tabelle se non esistono
# ---------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS sport (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS categorie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    nome TEXT NOT NULL,
    indennizzo REAL NOT NULL,
    FOREIGN KEY (sport_id) REFERENCES sport(id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS convocazioni (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_inizio TEXT,
    orario_partenza TEXT,
    sport TEXT,
    categoria TEXT,
    tipo_gara TEXT,
    squadre TEXT,
    luogo TEXT,
    trasferta REAL,
    indennizzo REAL,
    note TEXT)''')

cursor.execute("SELECT COUNT(*) FROM sport")
if cursor.fetchone()[0] == 0:
    sports = {
        "Inline-Hockey": [
            ("Senior", 80.0),
            ("Mini", 60.0),
            ("Novizi", 70.0),
            ("Novizi Elite", 90.0),
            ("Juniores", 100.0),
            ("Donne", 80.0),
            ("2a lega", 80.0),
            ("1a lega", 100.0),
            ("LNB", 120.0),
            ("LNA", 150.0)
        ],
        "Hockey su ghiaccio": [
            ("U13", 50.0),
            ("U15", 50.0),
            ("SWHL D", 80.0)
        ]
    }
    for sport_name, categories in sports.items():
        cursor.execute("INSERT INTO sport (nome) VALUES (?)", (sport_name,))
        sport_id = cursor.lastrowid
        for nome, indennizzo in categories:
            cursor.execute('''INSERT INTO categorie (sport_id, nome, indennizzo)
                             VALUES (?, ?, ?)''', (sport_id, nome, indennizzo))

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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sport ORDER BY nome")
    sport = cursor.fetchall()

    cursor.execute("SELECT * FROM categorie")
    categorie = cursor.fetchall()
    conn.close()

    # Costruisci dizionario {sport_id: [categorie]}
    categorie_by_sport = {}
    for cat in categorie:
        sport_id = cat["sport_id"]
        if sport_id not in categorie_by_sport:
            categorie_by_sport[sport_id] = []
        categorie_by_sport[sport_id].append({
            "nome": cat["nome"],
            "indennizzo": cat["indennizzo"]
        })



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
    categoria: str = Form(...),
    tipo_gara: str = Form(...),
    squadre: str = Form(...),
    luogo: str = Form(...),
    trasferta: float = Form(0.0),
    indennizzo: float = Form(...),
    note: str = Form("")
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO convocazioni (data_inizio, orario_partenza, sport, squadre, luogo, trasferta, indennizzo, note, tipo_gara)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_inizio, orario_partenza, sport, squadre, luogo, trasferta, indennizzo, note, tipo_gara
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
# Pagina con la lista degli sport disponibili
# ---------------------------
@app.get("/gestione-sport", response_class=HTMLResponse)
def gestione_sport(request: Request):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM sport ORDER BY nome")
    sport = cur.fetchall()
    cur.execute('''SELECT categorie.*, sport.nome as sport_nome FROM categorie
                   JOIN sport ON categorie.sport_id = sport.id
                   ORDER BY sport.nome, categorie.nome''')
    categorie = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("gestione-sport.html", {"request": request, "sport_list": sport, "sport_categorie": categorie})

# ---------------------------
# Endpoint per aggiungere un nuovo sport
# ---------------------------
@app.post("/add-sport")
def add_sport(nome: str = Form(...)):
    # Connessione al database e inserimento del nuovo sport
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sport (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()
    # Reindirizzamento alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

# ---------------------------
# Endpoint per aggiungere una nuova categoria
# ---------------------------
@app.post("/add-categoria")
def add_categoria(
    sport_id: int = Form(...),          # ID dello sport a cui appartiene la categoria
    nome_categoria: str = Form(...),   # Nome della categoria
    tipo_gara: str = Form(...),        # Tipo di gara (es. Regular season)
    indennizzo: float = Form(...)      # Indennizzo per la categoria
):
    # Connessione al database e inserimento della nuova categoria
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO categorie (sport_id, nome, tipo_gara, indennizzo)
                      VALUES (?, ?, ?, ?)''', (sport_id, nome_categoria, tipo_gara, indennizzo))
    conn.commit()
    conn.close()
    # Reindirizzamento alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

# ---------------------------
# Endpoint per eliminare una categoria
# ---------------------------
@app.post("/delete-categoria/{id}")
def delete_categoria(id: int):
    # Connessione al database ed eliminazione della categoria specificata
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorie WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    # Reindirizzamento alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

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
        ev.name = row[4]               
        ev.begin = data_inizio
        ev.end = data_inizio + timedelta(hours=2)
        ev.location = row[5]
        ev.description = row[8]        

        ev.alarms = [
            DisplayAlarm(trigger=partenza - data_inizio),  # X ore prima della partita (es: -2h)
            DisplayAlarm(trigger=timedelta(days=-1)),      # 1 giorno prima
        ]
        cal.events.add(ev)

    with open("data/calendario.ics", "w") as f:
        f.writelines(cal.serialize_iter())

    return FileResponse("data/calendario.ics", media_type='text/calendar')
