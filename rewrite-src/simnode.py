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

    def remove_input(self, node):
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

    def remove_input(self, node: SimNode):
        try:
            self.inputs.remove(node)
        except KeyError:
            pass


class Nand(SimNode):
    serialized_glyphs = ['u', 'r', 'd', 'l']

    def __init__(self):
        self.inputs = set()
        self.signal = False
        self.new_signal = False
        self.facing = 0

    def recalculate_io(self, my_coord, board):
        neighbour_coords = board.neighbour_coords(my_coord)

        # Here we split the neighbours into inputs and outputs
        output_coords = neighbour_coords.pop(self.facing)
        output = board.get(output_coords)

        # TODO BUG - Doesn't take into account directionality of inputs
        self.inputs = set(filter(None,
                                 [board.get(nc) for nc in neighbour_coords]))

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

    def remove_input(self, node: SimNode):
        try:
            self.inputs.remove(node)
        except KeyError:
            pass


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
