import logging
from graph.graph import Nand, Wire, Switch

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

    @classmethod
    def deserialize_from_string(cls, string):
        def f(x):
            if x == '.':
                return None
            # TODO Make all SimNodes have a `deserialize` method and just iterates through a list of all classes catching exceptions until you find one that deserializes. Stops us having deserialization logic scattered everywhere.
            elif x in '+-':
                w = Wire()
                w.deserialize(x)
                # TODO recursively merge wire here...?
                return w
            elif x in 'xo':
                s = Switch()
                s.deserialize(x)
                return s
            else:
                n = Nand()
                n.deserialize(x)
                return n

        rows = string.split('\n')
        blah = [list(map(f, list(x))) for x in rows]

        # TODO: Make this not dumb
        g = Grid(1,1)
        g.tiles = blah

        # Perform connected component labelling
        # g.merge_wire_groups()
        components = g.find_components()

        logger.debug(components)

        # Replace all the wires with one wire
        # TODO put this in a func, don't just write it here... Do this next
        # Be careful about other graph items linking to stuff... Is it really okay to just replace all the wires? Will other SimNodes still hold references?
        for label, coords in components['label_lookup'].items():
            logger.debug(f'label: {label} coords: {coords}')
            # Make a new wire for this wire group
            w = Wire()
            for coord in coords:
                x, y = coord
                g.tiles[y][x] = w

        return g

    @classmethod
    def deserialize_from_reader(cls, reader):

        data = reader.read()
        return cls.deserialize_from_string(data)

    def serialize(self, writer):
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                me = self.tiles[y][x]
                glyph = '.'
                if not me is None:
                    glyph = str(me)
                writer.write(glyph)
            writer.write('\n')

    def get_all_components(self):
        wires = set()
        nands = set()
        switches = set()
        for y in range(len(self.tiles)):
            for x in range(len(self.tiles[y])):
                tile = self.tiles[y][x]
                if isinstance(tile, Nand):
                    nands.add((x,y,tile))
                elif isinstance(tile, Wire):
                    wires.add(tile)
                elif isinstance(tile, Switch):
                    switches.add((x,y,tile))
        return (wires, nands, switches)

    def refresh_io(self, wires, nands, switches):
        for wire in wires:
            wire.inputs = set()
        for (x, y, nand) in nands:
            nand.inputs = set()
            facing_delta = nand.get_facing_delta()

            input_coords = self.get_neighbours_coords((x, y), facing_delta)
            input_wires = list(filter(lambda x: isinstance(x, Wire), [self.get(cx, cy) for (cx, cy) in input_coords]))
            nand.inputs = set(input_wires)

            output_wire = self.get(*add(facing_delta, (x,y)))
            if (isinstance(output_wire, Wire)):
                output_wire.inputs.add(nand)

            logger.debug(f'Input wires: {input_wires}')

        for (x, y, switch) in switches:
            output_coords = self.get_neighbours_coords((x, y))
            for wire in filter(lambda x: isinstance(x, Wire), [self.get(cx, cy) for (cx, cy) in output_coords]):
                wire.inputs.add(switch)

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
        new: SimNode
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

    def get_neighbours_coords(self, coords, without=None):
        neighbours_delta = [
            (-1,0),
            (1,0),
            (0,-1),
            (0,1)
        ]
        if without:
            neighbours_delta.remove(without)
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

    def tick(self, mechanism='a'):
        """ Ticks the grid world.

        TODO: This should be in the graph class...

        Parameters
        ----------
        mechanism : string
            The rules to use when ticking.

            a: Wire is a normal simnode with state
            b: Wire proxies the state of attached inputs
        """
        wires, nands, switches = self.get_all_components()
        logger.debug(f'STATE BEFORE:\nWires: {wires}\nNands: {nands}')

        # TODO This should not have to be done every time!
        # If groups are kept up to date as components are
        # added/removed, we don't need to call this.
        self.refresh_io(wires, nands, switches)

        if mechanism == 'a':
            nand_nodes = set([n[2] for n in nands])
            switch_nodes = set([s[2] for s in switches])
            simnodes = nand_nodes.union(wires).union(switch_nodes)
            for node in simnodes:
                node.calculate_new_state()
            for node in simnodes:
                node.tick()

        if mechanism == 'b':
            # Note that switches don't tick.
            # There is nothing in-sim that updates them.
            for (_, _, nand) in nands:
                nand.calculate_new_state()
                nand.tick()
            for wire in wires:
                wire.calculate_new_state()
                wire.tick()

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
