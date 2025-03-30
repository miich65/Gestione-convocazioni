from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Convocazione:
    id: Optional[int] = None
    data_inizio: Optional[datetime] = None
    orario_partenza: Optional[datetime] = None
    sport: str = ''
    categoria: str = ''
    tipo_gara: str = ''
    squadre: str = ''
    luogo: str = ''
    trasferta: float = 0.0
    indennizzo: float = 0.0
    note: str = ''

    def calcola_indennizzo_totale(self) -> float:
        """
        Calcola l'indennizzo totale considerando trasferta e indennizzo base
        """
        # Esempio di calcolo, puoi personalizzarlo
        return self.indennizzo + (self.trasferta * 0.5)

    def is_valid(self) -> bool:
        """
        Verifica se la convocazione ha tutti i dati necessari
        """
        return all([
            self.data_inizio,
            self.orario_partenza,
            self.sport,
            self.categoria,
            self.luogo
        ])