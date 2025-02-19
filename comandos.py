# Joao Oliveira 110532
# Pedro Ponte 98059
# Filipe Posio 80709
from enum import Enum


class Comandos(Enum):
    IDLE = ''
    MOVE_UP = 'w'
    MOVE_DOWN = 's'
    MOVE_LEFT = 'a'
    MOVE_RIGHT = 'd'
    SHOOT = 'A'