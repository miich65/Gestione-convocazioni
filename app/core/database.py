import sqlite3
import os
from typing import List, Dict, Any
from app.models.sport import Sport, Categoria
from app.models.convocazione import Convocazione

class DatabaseManager:
    def __init__(self, db_path: str = "app/data/convocazioni.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Inizializza il database e crea le tabelle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabella sport
            cursor.execute('''CREATE TABLE IF NOT EXISTS sport (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL)''')

            # Tabella categorie
            cursor.execute('''CREATE TABLE IF NOT EXISTS categorie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_id INTEGER NOT NULL,
                nome TEXT NOT NULL,
                indennizzo REAL NOT NULL,
                FOREIGN KEY (sport_id) REFERENCES sport(id))''')

            # Tabella convocazioni
            cursor.execute('''CREATE TABLE IF NOT EXISTS convocazioni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inizio TEXT,
                orario_partenza TEXT,
                sport TEXT,
                categoria TEXT,
                tipo_gara TEXT,
                squadre TEXT,
                luogo TEXT,
                trasferta REAL,
                indennizzo REAL,
                note TEXT)''')

            # Popola dati iniziali se necessario
            self._populate_initial_data(conn)

    def _populate_initial_data(self, conn):
        """Popola il database con dati iniziali"""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sport")
        if cursor.fetchone()[0] == 0:
            sports = {
                "Inline-Hockey": [
                    ("Senior", 80.0),
                    ("Mini", 60.0),
                    ("Novizi", 70.0),
                    ("Novizi Elite", 90.0),
                    ("Juniores", 100.0),
                ],
                "Hockey su ghiaccio": [
                    ("U13", 50.0),
                    ("U15", 50.0),
                ]
            }
            
            for sport_name, categories in sports.items():
                cursor.execute("INSERT INTO sport (nome) VALUES (?)", (sport_name,))
                sport_id = cursor.lastrowid
                for nome, indennizzo in categories:
                    cursor.execute('''INSERT INTO categorie (sport_id, nome, indennizzo)
                                     VALUES (?, ?, ?)''', (sport_id, nome, indennizzo))
            conn.commit()

    def get_connection(self):
        """Gestisce la connessione al database"""
        return sqlite3.connect(self.db_path)

    def get_all_sports(self) -> List[Sport]:
        """Recupera tutti gli sport con le loro categorie"""
        with self.get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.id as sport_id, s.nome as sport_nome, 
                       c.id as categoria_id, c.nome as categoria_nome, c.indennizzo
                FROM sport s
                LEFT JOIN categorie c ON s.id = c.sport_id
                ORDER BY s.nome, c.nome
            ''')
            
            sports_dict = {}
            for row in cursor.fetchall():
                sport_id = row['sport_id']
                if sport_id not in sports_dict:
                    sports_dict[sport_id] = Sport(
                        id=sport_id, 
                        nome=row['sport_nome']
                    )
                
                if row['categoria_id']:
                    categoria = Categoria(
                        id=row['categoria_id'],
                        nome=row['categoria_nome'],
                        indennizzo=row['indennizzo']
                    )
                    sports_dict[sport_id].add_categoria(categoria)
            
            return list(sports_dict.values())

    def add_sport(self, sport: Sport):
        """Aggiunge uno sport e le sue categorie"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Inserisci lo sport
                cursor.execute("INSERT INTO sport (nome) VALUES (?)", (sport.nome,))
                sport_id = cursor.lastrowid

                # Inserisci le categorie
                for categoria in sport.categorie:
                    cursor.execute('''
                        INSERT INTO categorie (sport_id, nome, indennizzo) 
                        VALUES (?, ?, ?)
                    ''', (sport_id, categoria.nome, categoria.indennizzo))
                
                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                raise ValueError(f"Sport {sport.nome} già esistente")