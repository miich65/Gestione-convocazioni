from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/gestione-sport", response_class=templates.TemplateResponse)
def gestione_sport(request: Request):
    """Pagina di gestione sport"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query per recuperare sport e categorie
    cursor.execute('''
        SELECT s.id as sport_id, s.nome as sport_nome, 
               c.id as categoria_id, c.nome as categoria_nome, c.indennizzo
        FROM sport s
        LEFT JOIN categorie c ON s.id = c.sport_id
        ORDER BY s.nome, c.nome
    ''')
    
    # Raggruppa i risultati
    sports = {}
    for row in cursor.fetchall():
        sport_id = row['sport_id']
        if sport_id not in sports:
            sports[sport_id] = {
                'id': sport_id,
                'nome': row['sport_nome'],
                'categorie': []
            }
        
        # Aggiungi categoria se esiste
        if row['categoria_id']:
            sports[sport_id]['categorie'].append({
                'id': row['categoria_id'],
                'nome': row['categoria_nome'],
                'indennizzo': row['indennizzo']
            })
    
    conn.close()

    return templates.TemplateResponse("gestione-sport.html", {
        "request": request, 
        "sport_list": list(sports.values())
    })

@router.post("/add-sport")
def add_sport(nome: str = Form(...)):
    """Aggiunge un nuovo sport"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO sport (nome) VALUES (?)", (nome,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Sport già esistente
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/update-sport/{sport_id}")
def update_sport(sport_id: int, nome: str = Form(...)):
    """Aggiorna un sport esistente"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE sport SET nome = ? WHERE id = ?", (nome, sport_id))
        conn.commit()
    except sqlite3.Error:
        # Gestisci eventuali errori
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/delete-sport/{sport_id}")
def delete_sport(sport_id: int):
    """Elimina uno sport"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        # Verifica se ci sono categorie associate
        cursor.execute("SELECT COUNT(*) FROM categorie WHERE sport_id = ?", (sport_id,))
        if cursor.fetchone()[0] > 0:
            # Impossibile eliminare sport con categorie
            return RedirectResponse("/gestione-sport?error=Impossibile+eliminare+sport+con+categorie+associate", status_code=303)
        
        # Elimina lo sport
        cursor.execute("DELETE FROM sport WHERE id = ?", (sport_id,))
        conn.commit()
    except sqlite3.Error:
        # Gestisci eventuali errori
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/add-categoria")
def add_categoria(
    sport_id: int = Form(...), 
    nome_categoria: str = Form(...), 
    indennizzo: float = Form(...)
):
    """Aggiunge una nuova categoria"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO categorie (sport_id, nome, indennizzo) 
            VALUES (?, ?, ?)
        ''', (sport_id, nome_categoria, indennizzo))
        conn.commit()
    except sqlite3.IntegrityError:
        # Categoria già esistente
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/update-categoria/{categoria_id}")
def update_categoria(
    categoria_id: int,
    sport_id: int = Form(...), 
    nome_categoria: str = Form(...), 
    indennizzo: float = Form(...)
):
    """Aggiorna una categoria esistente"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE categorie 
            SET sport_id = ?, nome = ?, indennizzo = ? 
            WHERE id = ?
        ''', (sport_id, nome_categoria, indennizzo, categoria_id))
        conn.commit()
    except sqlite3.Error:
        # Gestisci eventuali errori
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303)

@router.post("/delete-categoria/{categoria_id}")
def delete_categoria(categoria_id: int):
    """Elimina una categoria"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categorie WHERE id = ?", (categoria_id,))
        conn.commit()
    except sqlite3.Error:
        # Gestisci eventuali errori
        pass
    finally:
        conn.close()
    
    return RedirectResponse("/gestione-sport", status_code=303),

def get_sport_stats() -> List[Dict[str, Any]]:
    """
    Recupera le statistiche per sport e categorie con conteggio partite
    """
    conn = sqlite3.connect("app/data/convocazioni.db")
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

def get_sport_with_complete_details():
    """
    Recupera sport e categorie per la pagina di gestione
    """
    conn = sqlite3.connect("app/data/convocazioni.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query per recuperare sport e categorie con nome dello sport
    cursor.execute('''
        SELECT 
            s.id as sport_id, 
            s.nome as sport_nome, 
            c.id as categoria_id, 
            c.nome as categoria_nome, 
            c.indennizzo,
            (SELECT nome FROM sport WHERE id = c.sport_id) as categoria_sport_nome
        FROM sport s
        LEFT JOIN categorie c ON s.id = c.sport_id
        ORDER BY s.nome, c.nome
    ''')
    
    # Raggruppa i risultati
    sports = {}
    sport_categorie = []
    for row in cursor.fetchall():
        sport_id = row['sport_id']
        if sport_id not in sports:
            sports[sport_id] = {
                'id': sport_id,
                'nome': row['sport_nome'],
                'categorie': []
            }
        
        # Aggiungi categoria se esiste
        if row['categoria_id']:
            categoria = {
                'id': row['categoria_id'],
                'nome': row['categoria_nome'],
                'indennizzo': row['indennizzo'],
                'sport_id': sport_id,
                'sport_nome': row['categoria_sport_nome']
            }
            sports[sport_id]['categorie'].append(categoria)
            sport_categorie.append(categoria)
    
    conn.close()
    return list(sports.values()), sport_categorie

@router.get("/gestione-sport", response_class=templates.TemplateResponse)
def gestione_sport(request: Request):
    """Pagina di gestione sport con statistiche"""
    sport_list = get_sport_stats()
    
    # Recupera anche le categorie per il template
    _, sport_categorie = get_sport_with_complete_details()
    
    return templates.TemplateResponse("gestione-sport.html", {
        "request": request, 
        "sport_list": sport_list,
        "sport_categorie": sport_categorie
    })
