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


def get_sport_stats():
    """
    Recupera le statistiche per sport e categorie
    Calcola:
    - Numero totale di partite per sport
    - Numero di partite per categoria
    """
    conn = sqlite3.connect("app/data/convocazioni.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Query per recuperare sport, categorie e conteggio partite
    cursor.execute('''
        WITH sport_stats AS (
            SELECT 
                s.id as sport_id, 
                s.nome as sport_nome, 
                c.id as categoria_id, 
                c.nome as categoria_nome,
                c.indennizzo,
                COUNT(conv.id) as partite_categoria
            FROM sport s
            LEFT JOIN categorie c ON s.id = c.sport_id
            LEFT JOIN convocazioni conv ON s.nome = conv.sport AND c.nome = conv.categoria
            GROUP BY s.id, s.nome, c.id, c.nome, c.indennizzo
        ),
        total_sport_stats AS (
            SELECT 
                sport_id, 
                sport_nome, 
                SUM(partite_categoria) as partite_totali
            FROM sport_stats
            GROUP BY sport_id, sport_nome
        )
        SELECT 
            ss.*,
            tss.partite_totali
        FROM sport_stats ss
        JOIN total_sport_stats tss ON ss.sport_id = tss.sport_id
        ORDER BY ss.sport_nome, ss.categoria_nome
    ''')
    
    # Raggruppa i risultati
    sports = {}
    for row in cursor.fetchall():
        sport_id = row['sport_id']
        if sport_id not in sports:
            sports[sport_id] = {
                'id': sport_id,
                'nome': row['sport_nome'],
                'partite_totali': row['partite_totali'],
                'categorie': []
            }
        
        # Aggiungi categoria se esiste
        if row['categoria_id']:
            sports[sport_id]['categorie'].append({
                'id': row['categoria_id'],
                'nome': row['categoria_nome'],
                'indennizzo': row['indennizzo'],
                'partite': row['partite_categoria']
            })
    
    conn.close()
    return list(sports.values())

@router.get("/gestione-sport", response_class=templates.TemplateResponse)
def gestione_sport(request: Request):
    """Pagina di gestione sport con statistiche"""
    sport_list = get_sport_stats()
    
    return templates.TemplateResponse("gestione-sport.html", {
        "request": request, 
        "sport_list": sport_list
    })
