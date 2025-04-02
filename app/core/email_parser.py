"""
Parser delle email di convocazione
"""
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional, Tuple
import sqlite3

# Configura il logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Percorso del database
DB_PATH = "data/convocazioni.db"

def parse_convocazione_email(html_content: str) -> Dict[str, Any]:
    """
    Analizza l'HTML dell'email per estrarre i dati della convocazione.
    """
    try:
        # Pulisci il markup HTML rimuovendo caratteri di escape tipici delle email
        cleaned_html = html_content.replace('=\r\n', '').replace('=\n', '').replace('=3D', '=')
        
        # Usa BeautifulSoup per analizzare l'HTML
        soup = BeautifulSoup(cleaned_html, 'html.parser')
        
        # Trova le tabelle nell'email
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            logger.error("Non sono state trovate abbastanza tabelle nell'email")
            return None
        
        # La prima tabella contiene le informazioni sulla partita
        partita_table = tables[0]
        arbitri_table = tables[1]
        
        # Estrai i dati dalla tabella della partita
        partita_data = extract_partita_data(partita_table)
        
        # Estrai i dati dalla tabella degli arbitri
        arbitri_data = extract_arbitri_data(arbitri_table)
        
        # Unisci i dati in un unico dizionario
        convocazione = {**partita_data, "arbitri": arbitri_data}
        
        logger.info(f"Dati convocazione estratti: {convocazione}")
        return convocazione
    
    except Exception as e:
        logger.error(f"Errore durante il parsing dell'email: {e}")
        return None

def extract_partita_data(table) -> Dict[str, Any]:
    """
    Estrae i dati della partita dalla tabella.
    """
    # Mappa per trasformare i nomi dei campi estratti nei nomi dei campi del database
    field_mapping = {
        "indice": "indice",
        "competizione": "tipo_gara",
        "data_ora": "data_inizio",
        "squadre": "squadre",
        "pista": "luogo",
        "password": "password"
    }
    
    data = {}
    
    # Trova l'indice della partita (prima cella con rowspan)
    indice_cell = table.select_one('td[rowspan="3"]')
    if indice_cell:
        data["indice"] = indice_cell.text.strip()
    
    # Trova le righe della tabella
    rows = table.find_all('tr')
    
    # Estrai la competizione, data/ora e squadre dalla seconda riga
    if len(rows) > 1:
        cells = rows[1].find_all('td')
        if len(cells) > 2:
            data["competizione"] = cells[1].text.strip()
            
            # Estrai la data e ora
            data_ora_text = cells[2].text.strip()
            data_ora_match = re.match(r'(\w+) (\d+) (\w+) (\d+) - (\d+:\d+)', data_ora_text)
            
            if data_ora_match:
                giorno, giorno_n, mese, anno, ora = data_ora_match.groups()
                # Converti il mese da testo a numero
                mesi = {
                    'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04', 
                    'mag': '05', 'giu': '06', 'lug': '07', 'ago': '08', 
                    'set': '09', 'ott': '10', 'nov': '11', 'dic': '12'
                }
                mese_num = mesi.get(mese.lower()[:3], '01')  # Default a gennaio se non trovato
                
                # Formatta la data ISO
                data_iso = f"{anno}-{mese_num}-{giorno_n.zfill(2)}T{ora}:00"
                data["data_inizio"] = data_iso
                
                # Estrai anche l'orario di partenza (impostato 1 ora prima dell'inizio per default)
                try:
                    ora_partenza = ora.split(':')
                    ora_int = int(ora_partenza[0])
                    minuti = ora_partenza[1]
                    
                    # Sottrai un'ora per l'orario di partenza
                    ora_partenza_int = ora_int - 1
                    if ora_partenza_int < 0:
                        ora_partenza_int = 23  # Gestisci il caso di mezzanotte
                    
                    data["orario_partenza"] = f"{ora_partenza_int:02d}:{minuti}"
                except Exception as e:
                    logger.error(f"Errore nel calcolo dell'orario di partenza: {e}")
                    data["orario_partenza"] = "00:00"  # Default fallback
            
            # Estrai le squadre
            data["squadre"] = cells[3].text.strip()
    
    # Estrai il luogo dalla terza riga
    if len(rows) > 2:
        cells = rows[2].find_all('td')
        if len(cells) > 1:
            data["pista"] = cells[1].text.strip()
    
    # Estrai la password se presente
    if len(rows) > 3:
        cells = rows[3].find_all('td')
        if len(cells) > 1:
            data["password"] = cells[1].text.strip()
    
    # Mappa i nomi dei campi per il database
    result = {}
    for original_key, value in data.items():
        db_key = field_mapping.get(original_key, original_key)
        result[db_key] = value
    
    return result

def extract_arbitri_data(table) -> List[Dict[str, Any]]:
    """
    Estrae i dati degli arbitri dalla tabella.
    """
    arbitri = []
    
    # Trova le righe della tabella escludendo l'intestazione
    rows = table.find_all('tr')[1:]  # Salta l'intestazione
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            # Estrai i dati dell'arbitro
            arbitro = {
                "nome": cells[0].text.strip(),
                "funzione": cells[1].text.strip(),
                "tipo_convocazione": cells[2].text.strip(),
                "commento": cells[3].text.strip() if len(cells) > 3 else "",
                "contatti": extract_contatti(cells[4].text.strip()) if len(cells) > 4 else {}
            }
            arbitri.append(arbitro)
    
    return arbitri

def extract_contatti(contatti_text: str) -> Dict[str, str]:
    """
    Estrae le informazioni di contatto dal testo.
    """
    contatti = {}
    
    # Cerca l'email
    email_match = re.search(r'E-mail\s*:\s*([^\s/]+)', contatti_text)
    if email_match:
        contatti["email"] = email_match.group(1).strip()
    
    # Cerca il cellulare
    cell_match = re.search(r'Cellulare\s*:\s*([^/]+)', contatti_text)
    if cell_match:
        contatti["cellulare"] = cell_match.group(1).strip()
    
    # Cerca il telefono lavoro
    tel_match = re.search(r'Telefono lavoro\s*:\s*([^/]+)', contatti_text)
    if tel_match:
        contatti["telefono_lavoro"] = tel_match.group(1).strip()
    
    return contatti

def get_sport_categoria(competizione: str) -> Tuple[str, str, float]:
    """
    Determina lo sport e la categoria in base alla competizione.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Default values
    default_sport = "Inline-Hockey"
    default_categoria = "Senior"
    default_indennizzo = 80.0
    
    try:
        # Cerca lo sport in base al nome
        cursor.execute("SELECT id FROM sport WHERE nome = ?", (default_sport,))
        sport_row = cursor.fetchone()
        sport_id = sport_row['id'] if sport_row else None
        
        # Cerca la categoria in base al nome e allo sport_id
        if sport_id:
            categoria_map = {
                "SWISS CUP VET": "Senior",
                "Friendly Game": "Amichevole",
                "LNA": "LNA",
                "LNB": "LNB",
                "1a lega": "1a lega",
                "2a lega": "2a lega",
                "Novizi": "Novizi",
                "Novizi Elite": "Novizi Elite",
                "Mini": "Mini",
                "Juniores": "Juniores",
                "Donne": "Donne"
            }
            
            # Cerca una corrispondenza nella competizione
            categoria_trovata = default_categoria
            for key, value in categoria_map.items():
                if key.lower() in competizione.lower():
                    categoria_trovata = value
                    break
            
            # Ottieni l'indennizzo dalla categoria
            cursor.execute("""
                SELECT indennizzo FROM categorie 
                WHERE sport_id = ? AND nome = ?
            """, (sport_id, categoria_trovata))
            
            categoria_row = cursor.fetchone()
            if categoria_row:
                indennizzo = categoria_row['indennizzo']
            else:
                indennizzo = default_indennizzo
                
            return default_sport, categoria_trovata, indennizzo
        
        return default_sport, default_categoria, default_indennizzo
    
    except Exception as e:
        logger.error(f"Errore nel determinare sport e categoria: {e}")
        return default_sport, default_categoria, default_indennizzo
    finally:
        conn.close()