import logging
logger = logging.getLogger()
logname = 'output/gameplay.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(module)s %(levelno)s %(message)s',
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

    def recalculate_io(self, my_coords, board):
        """Add neighbouring SimNodes to my inputs. Inject myself into my neighbours inputs."""
        pass

class Wire(SimNode):
    serialized_glyphs = ['-']

    def __init__(self):
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

class Nand(SimNode):
    serialized_glyphs = ['u', 'r', 'd', 'l']

    def __init__(self):
        self.inputs = set()
        self.signal = False
        self.facing = 0

    def recalculate_io(self, my_coord, board):
        neighbour_nodes = [board.get(add(x, my_coord)) for x in board.neighbour_deltas()]

        # Here we split the neighbours into inputs and outputs
        output = neighbour_nodes.pop(self.facing)

        self.inputs = set(list(filter(lambda x: isinstance(x, SimNode), neighbour_nodes)))

        # Attempt to notify the output space (Not all nodes have inputs, or there may be nothing there)
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
        neighbour_nodes = [board.get(add(x, my_coord)) for x in board.neighbour_deltas()]
        for output in neighbour_nodes:
            # Attempt to notify the output space (Not all nodes have inputs, or there may be nothing there)
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
        self.node_cache = dict() # coord -> SimNode
        self.wire_cache = dict() # Wire -> [coords]
                                 # Keep track of coords 

        # coord1 -> wire1
        # coord2 -> wire1
        # coord3 -> node2

        # thus, inversely...

        # wire1 -> coord1, coord2
        # node2 -> coord3

    def initialize_grid(self, dimensions):
        (x, y) = dimensions
        self.grid = [[None] * x for iy in range(y)]

    def tick(self, mechanism='a'):
        """Ticks the sim. Could work in parallel. Only touches the graph_cache."""
        for node in self.node_cache:
            node.tick()
        for wire in self.wire_cache:
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
        """Places a SimNode on the board. This also performs any wire joining and IO updates."""
        if isinstance(node, Wire):
            self._grid_wire_join(coords, node)
        else:
            self._grid_wire_break(coords, node)

        self._grid_neighbour_io_refresh(coords)

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
                if not me is None:
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
        return [(0,-1), (1,0), (0,1), (-1,0)]

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

    def _grid_local_wire_join(self, coords, node: SimNode):
        """Join multiple wires into one if required"""
        # neighbouring_wires = filter(lambda x: isinstance(x, Wire), neighbours(coords))
        # new_wire = union_wires(neighbouring_wires + [node])
        pass

    def _grid_local_wire_break(self, coords):
        """Break a wire into multiple bits if required"""
        pass

    def _grid_local_io_refresh(self, coords):
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

                if isinstance(tile, Wire):
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
            group = find(data, i)  # Beware that this `find` mutates `data`!
                                   # Must `find` each element once first if you
                                   # want to operate on the list directly.
            if i != group:
                label_lookup[group] = label_lookup[group] + label_lookup[i]
                for t in label_lookup[i]:
                    tile_lookup[t] = group
                del label_lookup[i]

        # Component labelling complete!
        # Now we can do what we came here for - Let's replace all the wires so that each group is made up of the same Wire object.
        for label, coords in label_lookup.items():
            logger.debug(f'Wire group: {label} is made from coords: {coords}')
            wire = Wire()
            for (x,y) in coords:
                # Low-level wire replace.
                self.grid[y][x] = wire

    def _grid_global_io_refresh(self):
        wires, nodes = self._get_caches()
        for wire in wires:
            wire.inputs = set()
        for (x, y, node) in nodes:
            node.recalculate_io((x, y), self)
