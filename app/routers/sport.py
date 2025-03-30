from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from typing import List, Dict, Any

# Definisci il router
router = APIRouter()

# Percorso del database
DB_PATH = "data/convocazioni.db"

# Template
from main import templates

@router.get("/gestione-sport", response_class=HTMLResponse)
def gestione_sport(request: Request):
    """Pagina di gestione sport"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute("SELECT * FROM sport ORDER BY nome")

    sport = cur.fetchall()
    sport_dict = [dict(row) for row in sport]

    cur.execute('''SELECT categorie.*, sport.nome as sport_nome FROM categorie
                    JOIN sport ON categorie.sport_id = sport.id
                    ORDER BY sport.nome, categorie.nome''')
    
    categorie = cur.fetchall()
    categorie_dict = [dict(row) for row in categorie]

    conn.close()    
    
    return templates.TemplateResponse("gestione-sport.html", {
        "request": request,
        "sport_list": sport_dict,
        "sport_categorie": categorie_dict
    })

@router.post("/add-sport")
def add_sport(nome: str = Form(...)):
    """Aggiunge un nuovo sport"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sport (nome) VALUES (?)", (nome,))
    conn.commit()
    conn.close()
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/update-sport/{id}")
def update_sport(id: int, nome: str = Form(...)):
    """Aggiorna il nome di uno sport"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Aggiorna lo sport nel database
    cursor.execute("UPDATE sport SET nome = ? WHERE id = ?", (nome, id))
    
    conn.commit()
    conn.close()
    
    # Reindirizza alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/delete-sport/{id}")
def delete_sport(id: int):
    """Elimina uno sport se non ha categorie associate"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verifica se ci sono categorie associate
        cursor.execute("SELECT COUNT(*) FROM categorie WHERE sport_id = ?", (id,))
        categoria_count = cursor.fetchone()[0]
        
        if categoria_count > 0:
            conn.close()
            # Qui potresti voler gestire questo caso, magari con un messaggio di errore
            return RedirectResponse("/gestione-sport?error=Impossibile+eliminare+sport+con+categorie+associate", status_code=303)
        
        # Elimina lo sport
        cursor.execute("DELETE FROM sport WHERE id = ?", (id,))
        conn.commit()
    except sqlite3.Error as e:
        # Gestione degli errori
        conn.rollback()
        return RedirectResponse(f"/gestione-sport?error={str(e)}", status_code=303)
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/add-categoria")
def add_categoria(
    sport_id: int = Form(...),          # ID dello sport a cui appartiene la categoria
    nome_categoria: str = Form(...),    # Nome della categoria
    indennizzo: float = Form(...)       # Indennizzo per la categoria
):
    """Aggiunge una nuova categoria"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Modifica la query SQL per rimuovere tipo_gara
    cursor.execute('''INSERT INTO categorie (sport_id, nome, indennizzo)
                    VALUES (?, ?, ?)''', (sport_id, nome_categoria, indennizzo))
    
    conn.commit()
    conn.close()
    # Reindirizzamento alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/delete-categoria/{id}")
def delete_categoria(id: int):
    """Elimina una categoria"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorie WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    # Reindirizzamento alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/update-categoria/{id}")
def update_categoria(
    id: int,
    sport_id: int = Form(...),
    nome_categoria: str = Form(...),
    indennizzo: float = Form(...)
):
    """Aggiorna una categoria esistente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Aggiorna la categoria nel database
    cursor.execute("""
        UPDATE categorie 
        SET sport_id = ?, nome = ?, indennizzo = ? 
        WHERE id = ?
    """, (sport_id, nome_categoria, indennizzo, id))
    
    conn.commit()
    conn.close()
    
    # Reindirizza alla pagina di gestione sport
    return RedirectResponse("/gestione-sport", status_code=303)

def get_sport_stats() -> List[Dict[str, Any]]:
    """
    Recupera le statistiche per sport e categorie con conteggio partite
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query migliorata per prestazioni e chiarezza
    cursor.execute('''
        WITH categoria_stats AS (
            SELECT 
                c.sport_id, 
                c.id AS categoria_id,
                c.nome AS categoria_nome,
                c.indennizzo,
                (SELECT COUNT(*) 
                 FROM convocazioni conv 
                 WHERE conv.sport = (SELECT nome FROM sport WHERE id = c.sport_id) 
                   AND conv.categoria = c.nome
                ) AS partite_categoria
            FROM categorie c
        ),
        sport_stats AS (
            SELECT 
                s.id AS sport_id, 
                s.nome AS sport_nome,
                (SELECT SUM(partite_categoria) 
                 FROM categoria_stats cs 
                 WHERE cs.sport_id = s.id
                ) AS partite_totali
            FROM sport s
        )
        SELECT 
            ss.sport_id, 
            ss.sport_nome, 
            ss.partite_totali,
            cs.categoria_id,
            cs.categoria_nome,
            cs.indennizzo,
            cs.partite_categoria
        FROM sport_stats ss
        LEFT JOIN categoria_stats cs ON cs.sport_id = ss.sport_id
        ORDER BY ss.sport_nome, cs.categoria_nome
    ''')
    
    # Raggruppa i risultati
    sports = {}
    for row in cursor.fetchall():
        sport_id = row['sport_id']
        if sport_id not in sports:
            sports[sport_id] = {
                'id': sport_id,
                'nome': row['sport_nome'],
                'partite_totali': row['partite_totali'] or 0,
                'categorie': []
            }
        
        # Aggiungi categoria se esiste
        if row['categoria_id']:
            sports[sport_id]['categorie'].append({
                'id': row['categoria_id'],
                'nome': row['categoria_nome'],
                'indennizzo': row['indennizzo'],
                'partite': row['partite_categoria'] or 0
            })
    
    conn.close()
    return list(sports.values())