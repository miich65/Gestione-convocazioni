from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Categoria:
    id: Optional[int] = None
    nome: str = ''
    indennizzo: float = 0.0

@dataclass
class Sport:
    id: Optional[int] = None
    nome: str = ''
    categorie: List[Categoria] = None

    def __post_init__(self):
        if self.categorie is None:
            self.categorie = []

    def add_categoria(self, categoria: Categoria):
        """Aggiunge una categoria allo sport"""
        self.categorie.append(categoria)

    def get_categoria_by_name(self, nome: str) -> Optional[Categoria]:
        """Recupera una categoria per nome"""
        for categoria in self.categorie:
            if categoria.nome == nome:
                return categoria
        return None