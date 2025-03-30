from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def form_get(request: Request):
    """Pagina di inserimento convocazione"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Recupera gli sport
    cursor.execute("SELECT * FROM sport ORDER BY nome")
    sport_list = [dict(row) for row in cursor.fetchall()]

    # Recupera le categorie
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
        "sport_list": sport_list,
        "categorie_json": categorie_by_sport
    })

@router.get("/convocazioni", response_class=HTMLResponse)
def lista_convocazioni(request: Request):
    """Pagina con la lista delle convocazioni"""
    conn = sqlite3.connect("app/data/convocazioni.db")
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
    data_inizio: str = Form(...),
    orario_partenza: str = Form(...),
    sport: str = Form(...),
    categoria: str = Form(...),  # Assicurati che questo campo sia obbligatorio nel form
    tipo_gara: str = Form(...),
    squadre: str = Form(...),
    luogo: str = Form(...),
    trasferta: float = Form(0.0),
    indennizzo: float = Form(0.0),  # Imposta un valore di default
    note: str = Form("")
):
    """Salva una nuova convocazione"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    cursor = conn.cursor()

    try:
        # Salva la convocazione
        cursor.execute('''
            INSERT INTO convocazioni (
                data_inizio, orario_partenza, sport, categoria, 
                tipo_gara, squadre, luogo, trasferta, indennizzo, note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data_inizio, orario_partenza, sport, categoria, 
            tipo_gara, squadre, luogo, trasferta, indennizzo, note
        ))

        # Recupera gli sport per ricaricare il form
        cursor.execute("SELECT * FROM sport ORDER BY nome")
        sport_list = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM categorie")
        categorie = cursor.fetchall()

        conn.commit()
    except Exception as e:
        print(f"Errore durante l'inserimento: {e}")
        conn.rollback()
        # Gestisci l'errore, magari restituendo un messaggio
        return templates.TemplateResponse("form.html", {
            "request": request,
            "error": str(e),
            "sport_list": sport_list,
            "categorie_json": categorie_by_sport
        })
    finally:
        conn.close()

    # Ricostruisci il dizionario delle categorie
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
        "msg": "Convocazione salvata!",
        "sport_list": sport_list,
        "categorie_json": categorie_by_sport
    })

@router.post("/delete/{conv_id}")
def delete_convocazione(conv_id: int):
    """Elimina una convocazione"""
    conn = sqlite3.connect("app/data/convocazioni.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM convocazioni WHERE id=?", (conv_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/convocazioni", status_code=303)

@router.post("/update/{conv_id}")
def update_convocazione(
    conv_id: int,
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
    conn = sqlite3.connect("app/data/convocazioni.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE convocazioni
        SET data_inizio=?, orario_partenza=?, sport=?, categoria=?, 
            tipo_gara=?, squadre=?, luogo=?, trasferta=?, 
            indennizzo=?, note=?
        WHERE id=?
    """, (
        data_inizio, orario_partenza, sport, categoria, 
        tipo_gara, squadre, luogo, trasferta, 
        indennizzo, note, conv_id
    ))
    conn.commit()
    conn.close()
    return RedirectResponse("/convocazioni", status_code=303)