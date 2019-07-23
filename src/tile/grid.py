from enum import Enum, auto

class Tile(Enum):
    GROUND=0
    WIRE=auto()
    NAND_UP=auto()
    NAND_DOWN=auto()
    NAND_LEFT=auto()
    NAND_RIGHT=auto()

class Grid:
    def __init__(self):
        self.tiles = [[Tile.GROUND] * 20 for y in range(20)]

    def to_world(self):
        """
        Converts the grid into a graph representation
        """
        pass
