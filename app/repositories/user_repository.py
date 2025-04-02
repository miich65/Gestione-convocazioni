import sqlite3
from typing import Optional, List, Dict
from datetime import datetime

# Modelli
from models.user import UserInDB, UserCreate, UserUpdate

# Database
DB_PATH = "data/convocazioni.db"

def setup_auth_tables():
    """Inizializza le tabelle necessarie per l'autenticazione"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabella utenti
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'arbitro' CHECK(role IN ('admin', 'arbitro')),
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tabella sessioni
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Modifica la tabella convocazioni per aggiungere il riferimento utente
    try:
        cursor.execute("ALTER TABLE convocazioni ADD COLUMN user_id INTEGER DEFAULT NULL REFERENCES users(id)")
    except sqlite3.Error:
        pass
        
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> Optional[Dict]:
    """Recupera un utente dal database per username"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Recupera un utente dal database per email"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Recupera un utente dal database per ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    return dict(user) if user else None

def create_user(user: UserCreate, hashed_password: str, role: str = "arbitro") -> int:
    """Crea un nuovo utente nel database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO users (username, email, full_name, password, role) VALUES (?, ?, ?, ?, ?)",
        (user.username, user.email, user.full_name, hashed_password, role)
    )
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return user_id

def update_user(user_id: int, user_data: UserUpdate, hashed_password: Optional[str] = None) -> bool:
    """Aggiorna i dati di un utente"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if user_data.email is not None:
        updates.append("email = ?")
        params.append(user_data.email)
        
    if user_data.full_name is not None:
        updates.append("full_name = ?")
        params.append(user_data.full_name)
        
    if hashed_password is not None:
        updates.append("password = ?")
        params.append(hashed_password)
        
    if not updates:
        conn.close()
        return False
        
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    params.append(user_id)
    
    cursor.execute(query, params)
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success

def delete_user(user_id: int) -> bool:
    """Elimina un utente dal database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success

def store_token(user_id: int, token: str, expires_at: datetime) -> bool:
    """Salva un token nella tabella sessioni"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat())
    )
    
    conn.commit()
    conn.close()
    
    return True

def revoke_token(token: str) -> bool:
    """Revoca un token (per logout)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success

def list_users(skip: int = 0, limit: int = 100) -> List[Dict]:
    """Recupera una lista di utenti"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, username, email, full_name, role, is_active, created_at FROM users LIMIT ? OFFSET ?",
        (limit, skip)
    )
    
    users = [dict(user) for user in cursor.fetchall()]
    conn.close()
    
    return users