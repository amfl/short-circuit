from enum import Enum, auto

class Tile(Enum):
    GROUND=auto()
    WIRE=auto()
    NAND_UP=auto()

class Grid:
    def __init__(self):
        self.tiles = [[Tile.GROUND] * 20]*20

    def to_world(self):
        """
        Converts the grid into a graph representation
        """
        pass
