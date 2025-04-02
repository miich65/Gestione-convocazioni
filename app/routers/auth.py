from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from datetime import datetime, timedelta

from models.user import UserCreate, User
from core.auth.hashing import get_password_hash
from core.auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from core.auth.dependencies import (
    authenticate_user, get_current_active_user, 
    get_current_admin_user, get_current_user_from_cookie
)
import repositories.user_repository as user_repo

# Template (usa l'istanza condivisa per avere i filtri configurati)
from main import templates

router = APIRouter(tags=["auth"])

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Pagina di login"""
    # Verifica se l'utente è già autenticato
    current_user = get_current_user_from_cookie(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
        
    return templates.TemplateResponse("auth/login.html", {
        "request": request
    })

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False)
):
    """Gestisce il login e crea token JWT"""
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Username o password non validi"}
        )
    
    # Crea token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if remember:
        # Se "remember me" è selezionato, estendi a 30 giorni
        access_token_expires = timedelta(days=30)
        
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    # Salva token nel DB (per poterlo revocare in caso di logout)
    expire_date = datetime.utcnow() + access_token_expires
    user_repo.store_token(user.id, access_token, expire_date)
    
    # Imposta cookie e reindirizza
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),
        path="/",       # Assicurati che il cookie sia disponibile per tutto il sito
        samesite="lax"  # Importante per la sicurezza e per consentire redirezioni
    )
    
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Pagina di registrazione"""
    return templates.TemplateResponse("auth/register.html", {
        "request": request
    })

@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    full_name: str = Form(None)
):
    """Gestisce la registrazione nuovo utente"""
    # Verifica che le password corrispondano
    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/register.html", {
                "request": request,
                "error": "Le password non corrispondono",
                "username": username,
                "email": email,
                "full_name": full_name
            }
        )
    
    # Verifica che username e email non esistano già
    if user_repo.get_user_by_username(username):
        return templates.TemplateResponse(
            "auth/register.html", {
                "request": request,
                "error": "Username già in uso",
                "email": email,
                "full_name": full_name
            }
        )
        
    if user_repo.get_user_by_email(email):
        return templates.TemplateResponse(
            "auth/register.html", {
                "request": request,
                "error": "Email già in uso",
                "username": username,
                "full_name": full_name
            }
        )
    
    # Crea il nuovo utente
    user_data = UserCreate(
        username=username,
        email=email,
        full_name=full_name,
        password=password
    )
    
    hashed_password = get_password_hash(password)
    user_id = user_repo.create_user(user_data, hashed_password)
    
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "success": "Registrazione completata. Ora puoi accedere."}
    )

@router.get("/logout")
async def logout(request: Request):
    """Gestisce il logout"""
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
        # Revoca il token (non necessario ma buona pratica)
        user_repo.revoke_token(token)
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="access_token")
    return response

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, current_user: User = Depends(get_current_active_user)):
    """Pagina profilo utente"""
    return templates.TemplateResponse("auth/profile.html", {
        "request": request,
        "user": current_user
    })

@router.get("/users", response_class=HTMLResponse)
async def users_list(
    request: Request, 
    current_user: User = Depends(get_current_admin_user)
):
    """Pagina di gestione utenti (solo admin)"""
    users = user_repo.list_users()
    return templates.TemplateResponse("auth/users.html", {
        "request": request,
        "users": users
    })