"""
Client IMAP per leggere le email di convocazione
"""
import imaplib
import email
from email.header import decode_header
import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

# Importa il parser delle email
from core.email_parser import parse_convocazione_email, get_sport_categoria

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorso del database
DB_PATH = "data/convocazioni.db"

# Credenziali email (da sostituire con le tue)
EMAIL_USER = os.environ.get("EMAIL_USER", "mic.ferreira2004@gmail.com")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "0Nmyblock!")
EMAIL_SERVER = os.environ.get("EMAIL_SERVER", "imap.gmail.com")  # o imap.outlook.com per Outlook
EMAIL_FOLDER = os.environ.get("EMAIL_FOLDER", "skater")

# Filtri per la ricerca delle email
EMAIL_SEARCH_FROM = "noreply@sportwizz.ch"

def connect_to_server() -> Optional[imaplib.IMAP4_SSL]:
    """
    Connette al server IMAP e seleziona la cartella.
    """
    try:
        # Connessione al server
        mail = imaplib.IMAP4_SSL(EMAIL_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASSWORD)
        mail.select(EMAIL_FOLDER)
        return mail
    except Exception as e:
        logger.error(f"Errore nella connessione al server email: {e}")
        return None

def get_email_ids(mail: imaplib.IMAP4_SSL, criteria: str = "UNSEEN") -> List[str]:
    """
    Ottiene gli ID delle email in base ai criteri specificati.
    """
    try:
        # Cerca email non lette dal mittente specifico
        search_criteria = f'({criteria} FROM "{EMAIL_SEARCH_FROM}")'
        status, data = mail.search(None, search_criteria)
        
        if status != "OK":
            logger.error(f"Errore nella ricerca delle email: {status}")
            return []
        
        # Ottieni gli ID delle email trovate
        email_ids = data[0].split()
        return [email_id.decode() for email_id in email_ids]
    except Exception as e:
        logger.error(f"Errore nella ricerca delle email: {e}")
        return []

def get_email_content(mail: imaplib.IMAP4_SSL, email_id: str) -> Optional[Dict[str, Any]]:
    """
    Ottiene il contenuto di un'email in base all'ID.
    """
    try:
        # Recupera l'email completa
        status, data = mail.fetch(email_id.encode(), "(RFC822)")
        
        if status != "OK":
            logger.error(f"Errore nel recupero dell'email {email_id}: {status}")
            return None
        
        # Analizza l'email
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Estrai i dettagli dell'email
        subject = decode_email_header(msg["Subject"])
        from_addr = decode_email_header(msg["From"])
        date_str = decode_email_header(msg["Date"])
        
        logger.info(f"Email trovata: Da: {from_addr}, Oggetto: {subject}")
        
        # Estrai il contenuto HTML
        html_content = None
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html_content = part.get_payload(decode=True).decode()
                break
        
        if not html_content:
            logger.warning(f"Nessun contenuto HTML trovato nell'email {email_id}")
            return None
        
        return {
            "id": email_id,
            "subject": subject,
            "from": from_addr,
            "date": date_str,
            "html": html_content
        }
    except Exception as e:
        logger.error(f"Errore nel recupero del contenuto dell'email {email_id}: {e}")
        return None

def decode_email_header(header: str) -> str:
    """
    Decodifica l'intestazione dell'email.
    """
    if not header:
        return ""
    
    try:
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                decoded_part = part.decode(encoding or "utf-8", errors="replace")
            else:
                decoded_part = part
            decoded_parts.append(decoded_part)
        
        return " ".join(decoded_parts)
    except Exception as e:
        logger.error(f"Errore nella decodifica dell'intestazione: {e}")
        return header

def mark_email_as_read(mail: imaplib.IMAP4_SSL, email_id: str):
    """
    Segna un'email come letta.
    """
    try:
        mail.store(email_id.encode(), "+FLAGS", "\\Seen")
        logger.info(f"Email {email_id} segnata come letta")
    except Exception as e:
        logger.error(f"Errore nel segnare l'email {email_id} come letta: {e}")

def mark_email_as_processed(mail: imaplib.IMAP4_SSL, email_id: str):
    """
    Segna un'email come elaborata (opzionalmente sposta in una cartella).
    """
    try:
        # Opzione 1: segna come letta
        mail.store(email_id.encode(), "+FLAGS", "\\Seen")
        
        # Opzione 2: aggiungi un flag personalizzato
        mail.store(email_id.encode(), "+FLAGS", "Processed")
        
        # Opzione 3: spostala in una cartella "Elaborati" (decommentare se necessario)
        # mail.create("Elaborati")  # Crea la cartella se non esiste
        # mail.copy(email_id.encode(), "Elaborati")
        # mail.store(email_id.encode(), "+FLAGS", "\\Deleted")
        # mail.expunge()
        
        logger.info(f"Email {email_id} segnata come elaborata")
    except Exception as e:
        logger.error(f"Errore nel segnare l'email {email_id} come elaborata: {e}")

def save_convocazione(convocazione_data: Dict[str, Any]) -> int:
    """
    Salva la convocazione nel database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Estrai i dati principali
        indice = convocazione_data.get("indice", "")
        tipo_gara = convocazione_data.get("tipo_gara", "")
        data_inizio = convocazione_data.get("data_inizio", "")
        orario_partenza = convocazione_data.get("orario_partenza", "")
        squadre = convocazione_data.get("squadre", "")
        luogo = convocazione_data.get("luogo", "")
        
        # Determina lo sport e la categoria in base alla competizione
        sport, categoria, indennizzo = get_sport_categoria(tipo_gara)
        
        # Verifica se esiste già una convocazione con lo stesso indice
        cursor.execute("SELECT id FROM convocazioni WHERE squadre = ? AND data_inizio = ?", (squadre, data_inizio))
        existing = cursor.fetchone()
        
        if existing:
            # Aggiorna la convocazione esistente
            cursor.execute("""
                UPDATE convocazioni 
                SET tipo_gara = ?, sport = ?, categoria = ?, 
                    orario_partenza = ?, luogo = ?,
                    trasferta = ?, indennizzo = ?
                WHERE id = ?
            """, (
                tipo_gara, sport, categoria, 
                orario_partenza, luogo,
                0.0, indennizzo, existing[0]
            ))
            convocazione_id = existing[0]
            logger.info(f"Convocazione aggiornata con ID: {convocazione_id}")
        else:
            # Inserisci una nuova convocazione
            cursor.execute("""
                INSERT INTO convocazioni (
                    data_inizio, orario_partenza, sport, categoria, 
                    tipo_gara, squadre, luogo, trasferta, indennizzo, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data_inizio, orario_partenza, sport, categoria,
                tipo_gara, squadre, luogo, 0.0, indennizzo, 
                f"Importato automaticamente. Indice: {indice}"
            ))
            convocazione_id = cursor.lastrowid
            logger.info(f"Nuova convocazione inserita con ID: {convocazione_id}")
        
        conn.commit()
        return convocazione_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Errore nel salvare la convocazione: {e}")
        raise
    finally:
        conn.close()

def process_emails() -> List[int]:
    """
    Processa le email non lette e importa le convocazioni.
    """
    processed_ids = []
    
    # Connessione al server email
    mail = connect_to_server()
    if not mail:
        return processed_ids
    
    try:
        # Ottieni gli ID delle email non lette
        email_ids = get_email_ids(mail)
        logger.info(f"Trovate {len(email_ids)} email non lette")
        
        for email_id in email_ids:
            # Recupera il contenuto dell'email
            email_content = get_email_content(mail, email_id)
            
            if not email_content:
                continue
            
            # Analizza l'email per estrarre la convocazione
            convocazione_data = parse_convocazione_email(email_content["html"])
            
            if convocazione_data:
                # Salva la convocazione nel database
                convocazione_id = save_convocazione(convocazione_data)
                
                # Marca l'email come elaborata
                mark_email_as_processed(mail, email_id)
                
                processed_ids.append(convocazione_id)
            else:
                logger.warning(f"Impossibile estrarre i dati della convocazione dall'email {email_id}")
    
    finally:
        # Chiudi la connessione al server email
        try:
            mail.close()
            mail.logout()
        except Exception as e:
            logger.error(f"Errore nella chiusura della connessione email: {e}")
    
    return processed_ids

def check_emails_continuously(interval_seconds: int = 300):
    """
    Controlla le email continuamente con un intervallo specificato.
    """
    logger.info(f"Avvio del controllo continuo delle email ogni {interval_seconds} secondi")
    
    while True:
        try:
            logger.info("Controllo nuove email...")
            processed_ids = process_emails()
            
            if processed_ids:
                logger.info(f"Elaborate {len(processed_ids)} convocazioni: {processed_ids}")
                
                # Aggiorna il calendario
                try:
                    from routers.calendario import update_calendar_after_change
                    update_calendar_after_change()
                except Exception as e:
                    logger.error(f"Errore nell'aggiornamento del calendario: {e}")
            else:
                logger.info("Nessuna nuova convocazione trovata")
            
        except Exception as e:
            logger.error(f"Errore durante il controllo delle email: {e}")
        
        # Aspetta l'intervallo specificato
        time.sleep(interval_seconds)

if __name__ == "__main__":
    # Prova il processo una volta
    process_emails()