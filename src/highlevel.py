class SimNode:
    def get_output(self):
        return False

    def calculate_next_output(self):
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

class Nand(SimNode):
    serialized_glyphs = ['u', 'r', 'd', 'l']

    def __init__(self):
        self.state = False

    @classmethod
    def deserialize(cls, glyph):
        n = Nand()
        n.facing = cls.serialized_glyphs.index(glyph.lower())
        n.state = glyph.isupper()
        return n

class Switch(SimNode):
    serialized_glyphs = ['x', 'o']

    @classmethod
    def deserialize(cls, glyph):
        s = Switch()
        s.state = cls.serialized_glyphs.index(glyph)
        return s

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
        return self.grid[y][x]

    def set(self, coords, node: SimNode):
        """Places a SimNode on the board. This also performs any wire joining and IO updates."""
        if isinstance(node, Wire):
            self._grid_wire_join(coords, node)
        else:
            self._grid_wire_break(coords, node)

        self._grid_neighbour_io_refresh(coords)

    @classmethod
    def deserialize(cls, string):
        """Rebuilds the board from a string."""
        def f(glyph):
            for cls in [Wire, Nand, Switch]:
                try:
                    return cls.deserialize(glyph)
                except:
                    continue
            return None

        rows = string.split('\n')

        board = Board()
        board.grid = [list(map(f, list(x))) for x in rows]
        return board

    def serialize(self):
        """Dumps current grid state to a string."""
        pass

    #####################################################
    # Internal use methods
    #####################################################

    def _grid_wire_join(self, coords, node: SimNode):
        """Join multiple wires into one if required"""
        # neighbouring_wires = filter(lambda x: isinstance(x, Wire), neighbours(coords))
        # new_wire = union_wires(neighbouring_wires + [node])
        pass

    def _grid_wire_break(self, coords):
        """Break a wire into multiple bits if required"""
        pass

    def _grid_neighbour_io_refresh(self, coords):
        pass
