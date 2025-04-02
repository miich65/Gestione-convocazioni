"""
Router per l'importazione delle email di convocazione
"""
from fastapi import APIRouter, Request, BackgroundTasks, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import os
import threading
from datetime import datetime
import logging
from pydantic import BaseModel
from typing import List, Optional

# Importazioni dal progetto
from main import templates  # Usa l'istanza condivisa dei template
from core.email_client import process_emails, check_emails_continuously, save_convocazione
from core.email_parser import parse_convocazione_email
from routers.calendario import update_calendar_after_change

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definisci il router
router = APIRouter(prefix="/email-import")

# Modello per il log delle importazioni
class ImportLog(BaseModel):
    id: int
    timestamp: datetime
    email_id: Optional[str] = None
    subject: Optional[str] = None
    convocazione_id: Optional[int] = None
    status: str
    message: Optional[str] = None

# Percorso del database
DB_PATH = "data/convocazioni.db"

# Variabile globale per controllare il thread in background
email_check_thread = None
email_check_running = False

def setup_import_log_table():
    """
    Crea la tabella per il log delle importazioni se non esiste.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS email_import_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        email_id TEXT,
        subject TEXT,
        convocazione_id INTEGER,
        status TEXT NOT NULL,
        message TEXT
    )''')
    
    conn.commit()
    conn.close()

def log_import(email_id: str = None, subject: str = None, 
               convocazione_id: int = None, status: str = "unknown", 
               message: str = None):
    """
    Registra un log per l'importazione.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO email_import_log 
        (timestamp, email_id, subject, convocazione_id, status, message)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, email_id, subject, convocazione_id, status, message))
    
    conn.commit()
    conn.close()

@router.get("/", response_class=HTMLResponse)
async def email_import_page(request: Request):
    """
    Pagina per la gestione dell'importazione delle email.
    """
    # Assicurati che la tabella del log esista
    setup_import_log_table()
    
    # Ottieni lo stato del controllo email
    global email_check_running
    
    # Ottieni i log recenti
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM email_import_log
        ORDER BY timestamp DESC
        LIMIT 10
    ''')
    
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("email_import.html", {
        "request": request,
        "logs": logs,
        "check_running": email_check_running
    })

@router.post("/start-check")
async def start_email_check(background_tasks: BackgroundTasks):
    """
    Avvia il controllo delle email in background.
    """
    global email_check_thread, email_check_running
    
    if email_check_running:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Il controllo delle email è già in esecuzione"}
        )
    
    # Avvia un thread in background per controllare le email periodicamente
    def start_thread():
        global email_check_running
        email_check_running = True
        log_import(status="info", message="Avvio controllo email continuo")
        check_emails_continuously(interval_seconds=300)  # 5 minuti
    
    email_check_thread = threading.Thread(target=start_thread)
    email_check_thread.daemon = True  # Il thread si chiuderà quando l'app si chiude
    email_check_thread.start()
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Controllo email avviato"}
    )

@router.post("/stop-check")
async def stop_email_check():
    """
    Ferma il controllo delle email in background.
    """
    global email_check_running
    
    if not email_check_running:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Il controllo delle email non è in esecuzione"}
        )
    
    # Imposta la variabile di controllo a False per interrompere il ciclo
    email_check_running = False
    log_import(status="info", message="Interruzione controllo email")
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Controllo email interrotto"}
    )

@router.post("/check-now")
async def check_emails_now(background_tasks: BackgroundTasks):
    """
    Esegue il controllo delle email immediatamente.
    """
    # Esegui il controllo delle email in un task in background
    background_tasks.add_task(run_email_check)
    
    return JSONResponse(
        status_code=200,
        content={"status": "success", "message": "Controllo email avviato"}
    )

async def run_email_check():
    """
    Esegue il controllo delle email e registra i risultati.
    """
    try:
        # Registra l'inizio del controllo
        log_import(status="info", message="Avvio controllo email manuale")
        
        # Processa le email
        processed_ids = process_emails()
        
        if processed_ids:
            # Registra il successo
            for convocazione_id in processed_ids:
                log_import(
                    convocazione_id=convocazione_id,
                    status="success",
                    message=f"Convocazione importata con ID: {convocazione_id}"
                )
            
            # Aggiorna il calendario
            update_calendar_after_change()
            
            return processed_ids
        else:
            # Registra che non sono state trovate nuove email
            log_import(
                status="info",
                message="Nessuna nuova convocazione trovata"
            )
            return []
    
    except Exception as e:
        # Registra l'errore
        error_message = str(e)
        logger.error(f"Errore durante il controllo delle email: {error_message}")
        log_import(
            status="error",
            message=f"Errore durante il controllo delle email: {error_message}"
        )
        return []

@router.post("/manual-import")
async def manual_import(
    background_tasks: BackgroundTasks,
    html_content: str = Form(...)
):
    """
    Importa manualmente una convocazione da HTML.
    """
    try:
        # Analizza l'HTML per estrarre i dati della convocazione
        convocazione_data = parse_convocazione_email(html_content)
        
        if not convocazione_data:
            log_import(
                status="error",
                message="Impossibile estrarre i dati della convocazione dall'HTML fornito"
            )
            
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Impossibile estrarre i dati della convocazione"}
            )
        
        # Salva la convocazione nel database
        convocazione_id = save_convocazione(convocazione_data)
        
        # Registra il successo
        log_import(
            convocazione_id=convocazione_id,
            status="success",
            message=f"Convocazione importata manualmente con ID: {convocazione_id}"
        )
        
        # Aggiorna il calendario in background
        background_tasks.add_task(update_calendar_after_change)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success", 
                "message": "Convocazione importata con successo",
                "id": convocazione_id
            }
        )
    
    except Exception as e:
        # Registra l'errore
        error_message = str(e)
        logger.error(f"Errore durante l'importazione manuale: {error_message}")
        log_import(
            status="error",
            message=f"Errore durante l'importazione manuale: {error_message}"
        )
        
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Errore durante l'importazione: {error_message}"}
        )

@router.get("/stats")
async def import_stats():
    """
    Statistiche sulle importazioni.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ottieni statistiche generali
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
            MAX(timestamp) as last_check
        FROM email_import_log
    ''')
    
    stats = dict(cursor.fetchone())
    
    # Ottieni l'elenco delle ultime importazioni
    cursor.execute('''
        SELECT * FROM email_import_log
        WHERE status = 'success'
        ORDER BY timestamp DESC
        LIMIT 5
    ''')
    
    last_imports = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return JSONResponse(
        status_code=200,
        content={
            "stats": stats,
            "last_imports": last_imports
        }
    )

# Funzione per inizializzare il controllo automatico delle email all'avvio dell'app
def init_email_check():
    """
    Inizializza il controllo delle email all'avvio dell'app, se configurato.
    """
    # Verifica se è abilitato l'avvio automatico (tramite variabile d'ambiente)
    auto_start = os.environ.get("EMAIL_CHECK_AUTOSTART", "false").lower() == "true"
    
    if auto_start:
        global email_check_thread, email_check_running
        
        # Avvia un thread in background per controllare le email periodicamente
        def start_thread():
            global email_check_running
            email_check_running = True
            log_import(status="info", message="Avvio automatico controllo email")
            check_emails_continuously(interval_seconds=300)  # 5 minuti
        
        email_check_thread = threading.Thread(target=start_thread)
        email_check_thread.daemon = True  # Il thread si chiuderà quando l'app si chiude
        email_check_thread.start()
        
        logger.info("Controllo automatico email avviato all'inizializzazione dell'app")