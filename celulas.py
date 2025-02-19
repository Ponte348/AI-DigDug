# Joao Oliveira 110532
# Pedro Ponte 98059
# Filipe Posio 80709
from enum import Enum

class Celulas(Enum):
    PASSAGE = 0
    ROCK    = 1
    ENEMY   = 2
    AURA    = 3
    BOULDER = 4
    SAFE_AURA = 5
    BOULDER_BENEATH = 6
    FYGAR_FIRE = 7