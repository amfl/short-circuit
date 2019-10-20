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

    def serialize(self, writer):
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                glyph = '.'
                if isinstance(self.tiles[y][x], Wire):
                    glyph = 'x'
                writer.write(glyph)
            writer.write('\n')

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
            else:
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
        # Set of (label, label) connections for later merging
        connections = set()
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

                    neighbouring_labels = [x for x in [tile_lookup.get(left), tile_lookup.get(top)] if not x is None]
                    try:
                        my_label = min(neighbouring_labels)
                        if len(set(neighbouring_labels)) == 2:
                            connections.add((my_label, max(neighbouring_labels)))
                    except ValueError:
                        # Looks like there are no neighbouring labels, so this is a new group.
                        my_label = len(label_lookup)

                    tile_lookup[me] = my_label
                    label_lookup[my_label] = label_lookup.get(my_label, []) + [me]

        logger.debug('-- PRE-MERGES --')
        logger.debug(f'The grid before merges: {tile_lookup}')
        logger.debug(f'Connection list: {connections}')

        def find(data, i):
            if i != data[i]:
                data[i] = find(data, data[i])
            return data[i]

        def union(data, i, j):
            pi, pj = find(data, i), find(data, j)
            if pi != pj:
                data[pi] = pj

        data = list(range(len(label_lookup)))
        # Perform all the unions in the connection list
        for (i, j) in connections:
            union(data, i, j)

        for i in range(len(label_lookup)):
            group = find(data, i)  # Beware that this `find` mutates `data`!
                                   # Must `find` each element once first if you
                                   # want to operate on the list directly.
            if i != group:
                label_lookup[group] = label_lookup[group] + label_lookup[i]
                for t in label_lookup[i]:
                    tile_lookup[t] = group
                del label_lookup[i]

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
        if x < 0 or y < 0:
            # Must handle this explicitly, python is happy to negative index
            return None
        try:
            return self.tiles[y][x]
        except IndexError:
            return None

    def set(self, x: int, y: int, new_tile):
        try:
            self.tiles[y][x] = new_tile
        except IndexError:
            pass
