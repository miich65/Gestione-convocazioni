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
    
    # Ottieni la lista degli sport (per eventuali riferimenti nel modale)
    cursor.execute("SELECT * FROM sport ORDER BY nome")
    sport_list = [dict(row) for row in cursor.fetchall()]
    
    # Esegui una query che ottiene le convocazioni con JOIN per avere i nomi degli sport
    cursor.execute("""
        SELECT c.*, 
               s.nome as sport_nome,
               cat.nome as categoria_nome
        FROM convocazioni c
        LEFT JOIN sport s ON c.sport = s.id
        LEFT JOIN categorie cat ON c.categoria = cat.id
        ORDER BY c.data_inizio DESC
    """)
    
    # Se stai salvando direttamente i nomi e non gli ID, questa query alternativa potrebbe essere necessaria
    # cursor.execute("SELECT * FROM convocazioni ORDER BY data_inizio DESC")
    
    convocazioni_data = cursor.fetchall()
    convocazioni = []
    
    # Processa ogni convocazione
    for conv in convocazioni_data:
        conv_dict = dict(conv)
        
        # Se i campi sport e categoria contengono ID, sostituiscili con i nomi
        # Questo controllo è necessario perché la tua tabella potrebbe avere sia ID che nomi
        
        # Se sport è un ID numerico e abbiamo trovato un nome dal JOIN
        if isinstance(conv_dict.get("sport"), int) and conv_dict.get("sport_nome"):
            conv_dict["sport"] = conv_dict["sport_nome"]
            
        # Se categoria è un ID numerico e abbiamo trovato un nome dal JOIN
        if isinstance(conv_dict.get("categoria"), int) and conv_dict.get("categoria_nome"):
            conv_dict["categoria"] = conv_dict["categoria_nome"]
        
        convocazioni.append(conv_dict)
    
    conn.close()
    
    return templates.TemplateResponse("convocazioni.html", {
        "request": request, 
        "convocazioni": convocazioni,
        "sport_list": sport_list
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
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verifica se sport e categoria sono ID numerici o nomi
    sport_value = sport
    categoria_value = categoria
    
    # Se sport è un nome, cerca l'ID corrispondente
    try:
        sport_id = int(sport)
        # È già un ID, verifica se esiste
        cursor.execute("SELECT nome FROM sport WHERE id = ?", (sport_id,))
        sport_nome = cursor.fetchone()
        if sport_nome:
            sport_value = sport_nome["nome"]  # Salva il nome
    except ValueError:
        # È un nome, non un ID
        pass
    
    # Se categoria è un nome, cerca l'ID corrispondente
    try:
        categoria_id = int(categoria)
        # È già un ID, verifica se esiste
        cursor.execute("SELECT nome FROM categorie WHERE id = ?", (categoria_id,))
        categoria_nome = cursor.fetchone()
        if categoria_nome:
            categoria_value = categoria_nome["nome"]  # Salva il nome
    except ValueError:
        # È un nome, non un ID
        pass

    # Salva la convocazione (con i nomi, non gli ID)
    cursor.execute('''
        INSERT INTO convocazioni (data_inizio, orario_partenza, sport, categoria, tipo_gara, squadre, luogo, trasferta, indennizzo, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data_inizio, orario_partenza, sport_value, categoria_value, tipo_gara, squadre, luogo, trasferta, indennizzo, note
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
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Verifica se sport e categoria sono ID numerici o nomi
    sport_value = sport
    categoria_value = categoria
    
    # Se sport è un nome, cerca l'ID corrispondente
    try:
        sport_id = int(sport)
        # È già un ID, verifica se esiste
        cursor.execute("SELECT nome FROM sport WHERE id = ?", (sport_id,))
        sport_nome = cursor.fetchone()
        if sport_nome:
            sport_value = sport_nome["nome"]  # Salva il nome
    except ValueError:
        # È un nome, non un ID
        pass
    
    # Se categoria è un nome, cerca l'ID corrispondente
    try:
        categoria_id = int(categoria)
        # È già un ID, verifica se esiste
        cursor.execute("SELECT nome FROM categorie WHERE id = ?", (categoria_id,))
        categoria_nome = cursor.fetchone()
        if categoria_nome:
            categoria_value = categoria_nome["nome"]  # Salva il nome
    except ValueError:
        # È un nome, non un ID
        pass
    
    cursor.execute("""
        UPDATE convocazioni
        SET data_inizio=?, orario_partenza=?, sport=?, categoria=?, tipo_gara=?, squadre=?, luogo=?, trasferta=?, indennizzo=?, note=?
        WHERE id=?
    """, (
        data_inizio, orario_partenza, sport_value, categoria_value, tipo_gara, squadre, luogo, trasferta, indennizzo, note, conv_id
    ))
    
    conn.commit()
    conn.close()
    
    # Aggiorna il calendario in background
    background_tasks.add_task(update_calendar_after_change)
    
    return RedirectResponse("/convocazioni", status_code=303)