from fastapi import APIRouter
from fastapi.responses import JSONResponse
import sqlite3

# Definisci il router
router = APIRouter(prefix="/api")

# Percorso del database
DB_PATH = "data/convocazioni.db"

@router.get("/categorie")
async def get_categorie():
    """
    Restituisce tutte le categorie raggruppate per sport_id.
    Formato: {sport_id: [{id, nome, indennizzo}, ...], ...}
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM categorie ORDER BY nome")
    categorie = cursor.fetchall()
    
    # Raggruppa le categorie per sport_id
    categorie_by_sport = {}
    for cat in categorie:
        sport_id = cat["sport_id"]
        if sport_id not in categorie_by_sport:
            categorie_by_sport[sport_id] = []
        
        categorie_by_sport[sport_id].append({
            "id": cat["id"],
            "nome": cat["nome"],
            "indennizzo": cat["indennizzo"]
        })
    
    conn.close()
    return JSONResponse(content=categorie_by_sport)

@router.get("/sport")
async def get_sport():
    """
    Restituisce l'elenco di tutti gli sport.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sport ORDER BY nome")
    sport = cursor.fetchall()
    
    sport_list = []
    for s in sport:
        sport_list.append({
            "id": s["id"],
            "nome": s["nome"]
        })
    
    conn.close()
    return JSONResponse(content=sport_list)