import logging
logger = logging.getLogger()
logname = 'output/gameplay.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format=('%(asctime)s,%(msecs)d %(module)s '
                            '%(levelno)s %(message)s'),
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


def add(tup1, tup2):
    """
    TODO Replace me with something sensible
    """
    return (tup1[0] + tup2[0], tup1[1] + tup2[1])


class SimNode:
    def output(self):
        return False

    def calculate_next_output(self):
        pass

    def tick(self):
        pass

    def recalculate_io(self, my_coords, board):
        """Add neighbouring SimNodes to my inputs. Inject myself into my
        neighbours inputs."""
        pass


class Wire(SimNode):
    serialized_glyphs = ['-']

    def __init__(self):
        self.signal = False
        self.new_signal = False

        self.inputs = set()
        # Of all SimNodes, only Wire keeps track of its outputs.
        # It does this to ensure speedy split/join operations.
        self.outputs = set()
        self.pieces = set()
    # Thoughts:
    #  - Maintain a list of coords which this wire is comprised of
    #    Then we can refer to it when doing wire splits/joins?
    #  - Maintain a dict of coords -> neighbouring SimNodes as well as (or
    #    instead of) a set of inputs/outputs. Then we can do splits/joins
    #    without ever checking neighbours

    @classmethod
    def deserialize(cls, glyph):
        assert(glyph in cls.serialized_glyphs)
        return Wire()

    def serialize(self):
        return self.serialized_glyphs[0]

    def calculate_next_output(self):
        self.new_signal = any(x.output() for x in self.inputs)

    def tick(self):
        self.signal = self.new_signal

    def output(self):
        return self.signal


class Nand(SimNode):
    serialized_glyphs = ['u', 'r', 'd', 'l']

    def __init__(self):
        self.inputs = set()
        self.signal = False
        self.new_signal = False
        self.facing = 0

    def recalculate_io(self, my_coord, board):
        neighbour_nodes = board.neighbour_objs(my_coord)

        # Here we split the neighbours into inputs and outputs
        output = neighbour_nodes.pop(self.facing)

        self.inputs = set(filter(
            lambda x: isinstance(x, SimNode),
            neighbour_nodes))

        # Attempt to notify the output space (Not all nodes have inputs, or
        # there may be nothing there)
        try:
            output.inputs.add(self)
        except AttributeError:
            pass

    @classmethod
    def deserialize(cls, glyph):
        n = Nand()
        n.facing = cls.serialized_glyphs.index(glyph.lower())
        n.signal = glyph.isupper()
        return n

    def serialize(self):
        glyph = self.serialized_glyphs[self.facing]
        if self.output():
            glyph = glyph.upper()
        return glyph

    def output(self):
        return self.signal

    def calculate_next_output(self):
        outputs = [x.output() for x in self.inputs]
        logger.debug(f'nand: Outputs: {outputs}')
        self.new_signal = not all(outputs)
        logger.debug(f'nand: New signal: {self.new_signal}')

    def tick(self):
        self.signal = self.new_signal


class Switch(SimNode):
    serialized_glyphs = ['x', 'o']

    def __init__(self):
        self.signal = False

    @classmethod
    def deserialize(cls, glyph):
        s = Switch()
        s.signal = cls.serialized_glyphs.index(glyph)
        return s

    def serialize(self):
        return self.serialized_glyphs[self.output()]

    def output(self):
        return self.signal

    def recalculate_io(self, my_coord, board):
        neighbour_nodes = board.neighbour_objs(my_coord)
        for output in neighbour_nodes:
            # Attempt to notify the output space (Not all nodes have inputs, or
            # there may be nothing there)
            try:
                output.inputs.add(self)
            except AttributeError:
                pass


class Board:
    def __init__(self):
        # Multidimensional array
        self.grid = None
        # TODO Do I want a bidict?
        # coord -> SimNode, SimNode -> [coord]
        # Or some kind of horrible bidirectional multimap...
        # https://stackoverflow.com/questions/39624938/need-a-bidirectional-map-which-allows-duplicate-values-and-returns-list-of-valu
        self.node_cache = dict()  # coord -> SimNode
        self.wire_cache = dict()  # Wire -> [coords]

        # coord1 -> wire1
        # coord2 -> wire1
        # coord3 -> node2

        # thus, inversely...

        # wire1 -> coord1, coord2
        # node2 -> coord3

    def initialize_grid(self, dimensions):
        (x, y) = dimensions
        self.grid = [[None] * x for iy in range(y)]

    def tick(self):
        """Ticks the sim. Could work in parallel. Only touches the
        graph_cache."""
        wires, nodes = self._get_caches()
        logger.info(f'TICKING THE SIM')
        logger.debug(f'wires: {wires} nodes: {nodes}')

        for (_, _, node) in nodes:
            logger.debug(f'Ticking the node: {node}')
            node.calculate_next_output()
        # Because nodes can connect directly to other nodes, the tick step must
        # be separate from the calculation step. Otherwise, the unsorted nature
        # of the node set will produce non-deterministic behavior.
        for (_, _, node) in nodes:
            node.tick()
        for wire in wires:
            logger.debug(f'Ticking the wire: {wire}')
            wire.calculate_next_output()
            wire.tick()

    def get(self, coords):
        """Gets a SimNode or None via grid coords"""
        (x, y) = coords
        if x < 0 or y < 0:
            # Must handle this explicitly, python is happy to negative index
            return None
        try:
            return self.grid[y][x]
        except IndexError:
            return None

    def set(self, coords, node: SimNode):
        """Places a SimNode on the board. This also performs any wire joining
        and IO updates."""

        old_node = self.get(coords)
        self.set_basic(coords, node)

        # Break any wires we need to
        if isinstance(node, Wire):
            self._grid_local_wire_join(coords, node)
        else:
            self._grid_local_wire_break(coords, node)

        # Make sure all neighbours have their connections updated
        self._grid_local_io_refresh(coords)


    def set_basic(self, coords, node: SimNode):
        # Update the contents of the board with the new object
        x, y = coords
        if x < 0 or y < 0:
            raise IndexError
        self.grid[y][x] = node


    @classmethod
    def deserialize(cls, string):
        """Rebuilds the grid from a string."""

        def to_simnode(glyph):
            for cls in [Wire, Nand, Switch]:
                try:
                    return cls.deserialize(glyph)
                except:
                    continue
            return None

        rows = string.split('\n')

        board = Board()
        board.grid = [list(map(to_simnode, list(x))) for x in rows]

        board._grid_global_wire_join()
        board._grid_global_io_refresh()

        return board

    def serialize(self):
        """Dumps current grid state to a string."""
        string = ''
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                me = self.grid[y][x]
                glyph = '.'
                if me is not None:
                    glyph = me.serialize()
                string += glyph
            string += '\n'
        # Slice off the last newline otherwise we end up with two of them
        return string[:-1]

    #####################################################
    # Convenience methods
    #####################################################

    @classmethod
    def neighbour_deltas(cls):
        return [(0, -1), (1, 0), (0, 1), (-1, 0)]

    @classmethod
    def neighbour_coords(cls, coords):
        return [add(coords, x) for x in cls.neighbour_deltas()]

    def neighbour_objs(self, coords):
        return [self.get(c) for c in self.neighbour_coords(coords)]

    #####################################################
    # Internal use methods
    #####################################################

    def _get_caches(self):
        """Gets all data which SHOULD be cached (but atm isn't).
        TODO: Get rid of this method entirely, ideally"""
        wires = set()
        nodes = set()
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                me = self.grid[y][x]
                if isinstance(me, Wire):
                    wires.add(me)
                elif isinstance(me, SimNode):
                    nodes.add((x, y, me))
        return (wires, nodes)

    def _grid_local_wire_join(self, coords, new_wire: Wire):
        """Ensures all wires in the wire group at the given coords consist of
        the same object, and that inputs/outputs are correct.

        Parameters
        ----------
        coords : tuple
            A tuple of grid coordinates to join at.
        new_wire : Wire
            The new wire to replace the entire group with.
        """
        neighbouring_wires = [sn for sn in self.neighbour_objs(coords)
                              if isinstance(sn, Wire)]

        new_wire.signal = any([w.output() for w in neighbouring_wires])

        # Unioning N sets is ugly in python
        old_input_sets = [w.inputs for w in neighbouring_wires]
        try:
            new_wire.inputs = old_input_sets[0].union(*old_input_sets[1:])
        except IndexError:
            # It's possible there is no sets[0]
            new_wire.inputs = set()

        # TODO Replace this with cache lookups: wire group -> [coord]
        def _recursive_replace_wire(old_wire_coords, new_wire):
            old_node = self.get(old_wire_coords)
            if not isinstance(old_node, Wire):
                return

            # Replace the current wire
            x, y = old_wire_coords
            self.grid[y][x] = new_wire

            # In the list of all wire neighbours which aren't the new wire...
            for nc in self.neighbour_coords(old_wire_coords):
                nn = self.get(nc)
                if isinstance(nn, Wire) and nn != new_wire:
                    # Replace them, too!
                    _recursive_replace_wire(nc, new_wire)
        _recursive_replace_wire(coords, new_wire)

        return new_wire

    def _grid_local_wire_break(self, coords, new_node: SimNode):
        """Break a wire into multiple bits if required"""
        pass

    def _grid_local_io_refresh(self, coords):
        # Update neighbours
        neighbour_coords = self.neighbour_coords(coords)
        for nc in neighbour_coords:
            n = self.get(coords)
            try:
                n.recalculate_io(coords, self)
            except:
                pass

    def _grid_global_wire_join(self):
        """Globally reevaluates the grid and performs low-level wire joins.
        Only used for debugging or in deserialization.
        Does NOT fix inputs/outputs.
        Performs connected-component labeling to find groups of wires

        https://en.wikipedia.org/wiki/Connected-component_labeling#Two-pass
        """

        # Map of tiles to labels
        tile_lookup = {}
        # Map of labels to tiles
        label_lookup = {}
        # Set of (label, label) connections for later merging
        connections = set()

        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                me = (x, y)
                tile = self.grid[y][x]

                if not isinstance(tile, Wire):
                    continue

                left = tile_lookup.get((x-1, y))
                top = tile_lookup.get((x, y-1))

                neighbouring_labels = [x for x in [left, top] if x is not None]
                try:
                    my_label = min(neighbouring_labels)
                    if len(set(neighbouring_labels)) == 2:
                        connections.add(
                                (my_label, max(neighbouring_labels)))
                except ValueError:
                    # Looks like there are no neighbouring labels, so this is a
                    # new group.
                    my_label = len(label_lookup)

                # Add myself into the tile_lookup
                tile_lookup[me] = my_label
                # Add myself into the label_lookup
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
            # Beware that this `find` mutates `data`!
            # Must `find` each element once first if you want to operate on the
            # list directly.
            group = find(data, i)

            if i != group:
                label_lookup[group] = label_lookup[group] + label_lookup[i]
                for t in label_lookup[i]:
                    tile_lookup[t] = group
                del label_lookup[i]

        # Component labelling complete!
        # Now we can do what we came here for - Let's replace all the wires so
        # that each group is made up of the same Wire object.
        for label, coords in label_lookup.items():
            logger.debug(f'Wire group: {label} is made from coords: {coords}')
            wire = Wire()
            for (x, y) in coords:
                # Low-level wire replace.
                self.grid[y][x] = wire

    def _grid_global_io_refresh(self):
        wires, nodes = self._get_caches()
        for wire in wires:
            wire.inputs = set()
        for (x, y, node) in nodes:
            node.recalculate_io((x, y), self)

        # Tick all the wires so they are all are up to date
        # Remember wires are direct proxies for the output of their inputs
        for wire in wires:
            wire.calculate_next_output()
            wire.tick()
