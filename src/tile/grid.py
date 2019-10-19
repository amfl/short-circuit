import logging
from graph.graph import Nand, Wire

logger = logging.getLogger()

def add(tup1, tup2):
    """
    TODO Replace me with something sensible
    """
    return (tup1[0] + tup2[0], tup1[1] + tup2[1])

class Grid:
    next_available_label = 0

    def __init__(self, x, y):
        self.tiles = [[None] * x for iy in range(y)]

    def get_all_wire(self):
        """Returns a list of all wire in the current grid."""
        result = []
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                tile = self.get(x, y)
                if (isinstance(tile, Wire)):
                    result.append(tile)
        return result

    def change_tile(self, coords, new):
        """
        Changes a tile, performing any joins that need to occur as a
        result.

        Parameters
        ----------
        coords : tuple
            A tuple of grid coordinates.
        new: Wire
            The new grid cell, or `None`. If it is wire, it is
            assumed to be an entirely new wire object. This method
            will take care of joining/deduplicating.
        """
        self.tiles[coords[1]][coords[0]] = new

        neighbours_coords = self.get_neighbours_coords(coords)
        nearby_tiles = [self.get(*coords) for coords in neighbours_coords]
        logger.debug(f"Nearby tiles: {nearby_tiles}")
        nearby_alien_wire = [t for t in nearby_tiles if isinstance(t, Wire)]
        if len(nearby_alien_wire) > 0:
            # If we are placing new wire, we have to recursively join the
            # neighbouring wires together.
            if isinstance(new, Wire):
                # Neighbouring wires will become whichever had the lowest label.
                get_new_wire = lambda: min(nearby_alien_wire, key=lambda x: x.label)

            # If we are deleting a piece of wire, we may have to break up
            # neighbouring wires into different wires.
            elif new == None:
                get_new_wire = lambda: Wire()

            # TODO Inefficiency - Have to iterate all neighbours again
            # because we don't know which of these are actualy wire.
            for nc in neighbours_coords:
                self.recursive_replace_wire(nc, get_new_wire())

    def recursive_replace_wire(self, old_wire_coords, new_wire):
        old_tile = self.get(*old_wire_coords)
        if not isinstance(old_tile, Wire):
            return

        # Replace the current wire
        self.set(*old_wire_coords, new_wire)

        # In the list of all wire neighbours which aren't the new wire...
        for nc in self.get_neighbours_coords(old_wire_coords):
            tile = self.get(*nc)
            if isinstance(tile, Wire) and tile != new_wire:
                # Replace them, too!
                self.recursive_replace_wire(nc, new_wire)

    def get_neighbours_coords(self, coords):
        neighbours_delta = [
            (-1,0),
            (1,0),
            (0,-1),
            (0,1)
        ]
        return [add(t, coords) for t in neighbours_delta]

    def to_world(self):
        """
        Converts the grid into a graph representation
        """
        pass

    def find_components(self):
        """
        Performs connected-component labeling to find groups of wires

        https://en.wikipedia.org/wiki/Connected-component_labeling#Two-pass
        """

        # Map of tiles to labels
        tile_lookup = {}
        # Map of labels to tiles
        label_lookup = {}
        # Map of labels to labels for later merging
        merge = {}
        # Map of NANDs
        nands = []

        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                me = (x, y)
                tile = self.tiles[y][x]

                if isinstance(tile, Nand):
                    nands.append(me)

                elif isinstance(tile, Wire):
                    left = (x-1, y)
                    top = (x, y-1)

                    try:
                        if isinstance(self.get(*left), Wire):
                            label = tile_lookup[left]
                            label_top = tile_lookup[top]  # can cause IndexError
                            if label_top != label:
                                merge[min(label_top, label)] = max(label_top, label)
                        elif isinstance(self.get(*top), Wire):
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
            label_lookup[k] = label_lookup[k] + label_lookup[v]
            for t in label_lookup[v]:
                tile_lookup[t] = k
            del label_lookup[v]

        return {
                'label_lookup': label_lookup,
                'tile_lookup': tile_lookup,
                'nands': nands
                }

    def get(self, x: int, y: int):
        """
        Useful in connected-component labeling so we don't go out of
        bounds
        """
        try:
            return self.tiles[y][x]
        except IndexError:
            return None

    def set(self, x: int, y: int, new_tile):
        try:
            self.tiles[y][x] = new_tile
        except IndexError:
            pass
