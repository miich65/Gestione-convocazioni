from passlib.context import CryptContext

# Configurazione per l'hashing delle password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica che la password corrisponda all'hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash da una password"""
    return pwd_context.hash(password)