from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt

# Configurazione token
SECRET_KEY = "da-cambiare-in-produzione-con-chiave-sicura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 ore

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica un token JWT"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])