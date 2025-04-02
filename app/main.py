# ---------------------------
# Applicazione FastAPI per gestire convocazioni arbitrali
# ---------------------------

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import sqlite3
import os

# Import del filtro dei template
from core.template_filters import setup_template_filters

# Inizializzazione dell'app FastAPI
app = FastAPI(title="Gestione Convocazioni Arbitrali")

# ---------------------------
# Configurazione del database SQLite
# ---------------------------
DB_PATH = "data/convocazioni.db"
os.makedirs("data", exist_ok=True) 

# ---------------------------
# Configurazione delle statiche e dei template HTML
# ---------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

templates = Jinja2Templates(directory="templates")
setup_template_filters(templates)

# ---------------------------
# Connessione al database e creazione delle tabelle se non esistono
# ---------------------------
def setup_database():
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

# Setup iniziale del database
setup_database()

# ---------------------------
# Importa tutte le rotte
# ---------------------------
from routers import convocazioni, sport, calendario, api, email_import

# Includi i router
app.include_router(convocazioni.router, tags=["Convocazioni"])
app.include_router(sport.router, tags=["Sport"])
app.include_router(calendario.router, tags=["Calendario"])
app.include_router(api.router, tags=["API"])
app.include_router(email_import.router, tags=["Email Import"])

# Inizializza il controllo automatico delle email
email_import.init_email_check()

# Se l'app viene eseguita direttamente
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)