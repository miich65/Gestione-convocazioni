from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3

# Importa la funzione per aggiornare il calendario
from routers.calendario import update_calendar_after_change

# Definisci il router
router = APIRouter()

# Percorso del database
DB_PATH = "data/convocazioni.db"

# Template (usa l'istanza condivisa per avere i filtri configurati)
from main import templates

@router.get("/", response_class=HTMLResponse)
def form_get(request: Request):
    """Pagina di inserimento convocazione"""
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

    return templates.TemplateResponse("form.html", {
        "request": request,
        "sport_list": sport,
        "categorie_json": categorie_by_sport
    })


@router.get("/convocazioni", response_class=HTMLResponse)
def lista_convocazioni(request: Request):
    """Pagina con la lista delle convocazioni"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM convocazioni ORDER BY data_inizio DESC")
    convocazioni = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("convocazioni.html", {
        "request": request, 
        "convocazioni": convocazioni
    })

@router.post("/add")
def form_post(
    request: Request,
    background_tasks: BackgroundTasks,
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
    """Salva una nuova convocazione"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Importante! Imposta row_factory per avere dict-like objects
    cursor = conn.cursor()

    # Salva la convocazione
    cursor.execute('''
        INSERT INTO convocazioni (data_inizio, orario_partenza, sport, categoria, tipo_gara, squadre, luogo, trasferta, indennizzo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_inizio, orario_partenza, sport, categoria, tipo_gara, squadre, luogo, trasferta, indennizzo, note
    ))

    # Prepara i dati per ricaricare il form
    cursor.execute("SELECT * FROM sport ORDER BY nome")
    sport_list = cursor.fetchall()

    cursor.execute("SELECT * FROM categorie")
    categorie = cursor.fetchall()

    conn.commit()
    conn.close()

    # Costruisci dizionario {sport_id: [categorie]}
    categorie_by_sport = {}
    for cat in categorie:
        # Accedi agli elementi come dict (dato che abbiamo impostato row_factory)
        sport_id = cat["sport_id"]
        if sport_id not in categorie_by_sport:
            categorie_by_sport[sport_id] = []
        categorie_by_sport[sport_id].append({
            "nome": cat["nome"],
            "indennizzo": cat["indennizzo"]
        })
    
    # Aggiorna il calendario in background
    background_tasks.add_task(update_calendar_after_change)

    return templates.TemplateResponse("form.html", {
        "request": request,
        "msg": "Convocazione salvata!",
        "sport_list": sport_list,
        "categorie_json": categorie_by_sport
    })

@router.post("/delete/{conv_id}")
def delete_convocazione(conv_id: int, background_tasks: BackgroundTasks):
    """Elimina una convocazione"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM convocazioni WHERE id=?", (conv_id,))
    conn.commit()
    conn.close()
    
    # Aggiorna il calendario in background
    background_tasks.add_task(update_calendar_after_change)
    
    return RedirectResponse("/convocazioni", status_code=303)

@router.post("/update/{conv_id}")
def update_convocazione(
    conv_id: int,
    background_tasks: BackgroundTasks,
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
    """Aggiorna una convocazione esistente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE convocazioni
        SET data_inizio=?, orario_partenza=?, sport=?, categoria=?, tipo_gara=?, squadre=?, luogo=?, trasferta=?, indennizzo=?, note=?
        WHERE id=?
    """, (
        data_inizio, orario_partenza, sport, categoria, tipo_gara, squadre, luogo, trasferta, indennizzo, note, conv_id
    ))
    conn.commit()
    conn.close()
    
    # Aggiorna il calendario in background
    background_tasks.add_task(update_calendar_after_change)
    
    return RedirectResponse("/convocazioni", status_code=303)