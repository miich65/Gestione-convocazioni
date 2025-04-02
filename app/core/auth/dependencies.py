from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from typing import Optional

from models.user import User, TokenData
from core.auth.jwt import decode_token
import repositories.user_repository as user_repo
from core.auth.hashing import verify_password

# OAuth2 scheme per proteggere le rotte
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Autentica utente con username e password"""
    user = user_repo.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["password"]):
        return None
    if not user["is_active"]:
        return None
    
    # Converti il dizionario in un oggetto User
    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        is_active=user["is_active"]
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Verifica token e restituisce l'utente corrente"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Prima prova a ottenere il token dal cookie
        request = Request()
        cookie_token = request.cookies.get("access_token")
        if cookie_token and cookie_token.startswith("Bearer "):
            token = cookie_token.replace("Bearer ", "")
        
        # Se non c'è un token, solleva eccezione
        if not token:
            raise credentials_exception
            
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username, role=payload.get("role"))
    except Exception:
        raise credentials_exception
        
    user = user_repo.get_user_by_username(username=token_data.username)
    if user is None or not user["is_active"]:
        raise credentials_exception
        
    # Converti il dizionario in un oggetto User
    return User(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        role=user["role"],
        is_active=bool(user["is_active"])
    )

def get_current_user_from_cookie(request: Request) -> Optional[User]:
    """Estrae l'utente dal cookie access_token."""
    token = request.cookies.get("access_token")
    print(f"Cookie token: {token}")  # Debug
    
    if not token:
        return None
        
    if not token.startswith("Bearer "):
        return None
        
    token = token.replace("Bearer ", "")
    
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        
        if not username:
            return None
            
        user_data = user_repo.get_user_by_username(username)
        if not user_data:
            return None
            
        return User(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data.get("full_name", ""),
            role=user_data["role"],
            is_active=bool(user_data["is_active"])
        )
    except Exception as e:
        print(f"Errore decodifica token: {str(e)}")  # Debug
        return None

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Verifica che l'utente sia attivo"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utente disattivato")
    return current_user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verifica che l'utente sia un amministratore"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permessi insufficienti"
        )
    return current_user