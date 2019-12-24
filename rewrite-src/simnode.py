import util
import logging
logger = logging.getLogger()


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

    def input_remove(self, node):
        pass

    def input_add(self, node, coord_delta):
        """Adds another node to my inputs if possible.

        Sometimes directionality is important when joining, so SimNodes must be
        able to define their connection strategies via this method.

        Arguments:
            node (SimNode): The new node to be added
            coord_delta: Coord difference between the two nodes

        Returns:
            bool: True if the node was added, False otherwise.
        """
        return False

    def outputs_to(self, coord_delta):
        """Whether this node can output in the given direction"""
        return True


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

    def input_remove(self, node: SimNode):
        try:
            self.inputs.remove(node)
        except KeyError:
            pass

    def input_add(self, node: SimNode, coord_delta):
        self.inputs.add(node)


class Nand(SimNode):
    serialized_glyphs = ['u', 'r', 'd', 'l']

    def __init__(self):
        self.inputs = set()
        self.signal = False
        self.new_signal = False
        self.facing = 0

    def recalculate_io(self, my_coord, board):
        # Reset inputs as empty, then slowly repopulate
        self.inputs = set()
        # Need to keep track of outputs so we don't immediately remove
        # ourselves again if many neighbour tiles are the same input AND
        # output object (eg, in the case of a simple 1-tick nand clock)
        outputs = set()
        deltas = util.neighbour_deltas()

        for i, delta in enumerate(deltas):
            nc = util.add(delta, my_coord)
            n = board.get(nc)

            if n is not None:
                if i == self.facing:
                    n.input_add(self, util.invert(delta))
                    outputs.add(n)
                else:
                    if n not in outputs:
                        n.input_remove(self)
                    if n.outputs_to(util.invert(delta)):
                        self.inputs.add(n)

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

    def input_remove(self, node: SimNode):
        try:
            self.inputs.remove(node)
        except KeyError:
            pass

    def input_add(self, node: SimNode, coord_delta):
        # Don't try and add inputs if they are located on your output side!
        if not self.outputs_to(coord_delta):
            self.inputs.add(node)
            return True

        return False

    def outputs_to(self, coord_delta):
        return util.neighbour_deltas()[self.facing] == coord_delta

    def rotate_facing(self, delta: int, my_coords, board):
        self.facing = (self.facing + delta) % 4

        self.recalculate_io(my_coords, board)


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
