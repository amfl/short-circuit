from enum import Enum, auto
import logging

logger = logging.getLogger()

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

    def find_wire_groups(self):
        """
        Performs connected-component labeling to find groups of wires

        https://en.wikipedia.org/wiki/Connected-component_labeling#Two-pass
        """

        # Map of tiles to labels
        tile_lookup = {}  # TODO: UNUSED
        # Map of labels to tiles
        label_lookup = {}
        # Map of labels to labels for later merging
        merge = {}

        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                tile = self.tiles[y][x]
                if tile is Tile.WIRE:
                    me = (x, y)
                    left = (x-1, y)
                    top = (x, y-1)

                    try:
                        if self.get(*left) == tile:
                            label = tile_lookup[left]
                            label_top = tile_lookup[top]  # can cause IndexError
                            if label_top != label:
                                merge[min(label_top, label)] = max(label_top, label)
                        elif self.get(*top) == tile:
                            label = tile_lookup[top]
                            label_left = tile_lookup[left]  # can cause IndexError
                            if label_left != label:
                                merge[min(label_left, label)] = max(label_left, label)
                        else:
                            label = len(label_lookup)
                    except KeyError:
                        pass
                    tile_lookup[me] = label
                    label_lookup[label] = label_lookup.get(label, []) + [me]

        # Perform merges
        for k, v in merge.items():
            # logger.debug(k, v)
            label_lookup[k] = label_lookup[k] + label_lookup[v]
            del label_lookup[v]

        return label_lookup

    def get(self, x: int, y: int):
        """
        Useful in connected-component labeling so we don't go out of
        bounds
        """
        try:
            return self.tiles[y][x]
        except IndexError:
            return GROUND
