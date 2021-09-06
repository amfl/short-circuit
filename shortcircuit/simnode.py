import logging
import json

import shortcircuit.util as util

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

    def state_obj(self):
        """An object which represents this object's current state. Is used for
        inspecting a SimNode for debugging."""
        state = {
            self.__class__.__name__: hex(id(self)),
            "signal": self.output()
        }
        if hasattr(self, 'inputs'):
            state["inputs"] = [hex(id(x)) for x in self.inputs]
        return state

    def __repr__(self):
        return json.dumps(self.state_obj())

    def get(self, q_board, my_coords, q_coord_delta):
        """Get the node and frame of reference (board/coord combo) which this
        node wants to present to the queryer, when approached at
        `q_coord_delta`. For most nodes, the frame of reference does not
        change, and the returned node is `self`. However, some special nodes
        act as portals and will defer to other nodes when attempts are made to
        access them. WireBridges are such a node - Attempting to read it from
        the side will result in returning whatever lies on the opposite side.

        Parameters
        ----------

        q_board : Board
          The board that the querying node is from
        my_coords : tuple
          The coords that the querying node perceives this node to have
        q_coord_delta : tuple
          The direction the querying node went to reach me
        """
        # h a v e   y o u   e v e r   s e e n   a   p o r t a l
        return (q_board, my_coords, self)


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
        return cls()

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


class WireBridge(SimNode):
    serialized_glyphs = ['|']

    def output(self):
        # A bridge should never be asked for output by another node, because
        # nothing will ever connect to it. It may be asked by a UI.
        return False

    @classmethod
    def deserialize(cls, glyph):
        assert(glyph in cls.serialized_glyphs)
        return cls()

    def serialize(self):
        return self.serialized_glyphs[0]

    def get(self, q_board, my_coords, q_coord_delta):
        new_coords = util.add(my_coords, q_coord_delta)
        new_node = q_board.get(new_coords)
        try:
            return new_node.get(q_board, new_coords, q_coord_delta)
        except AttributeError:
            return (q_board, my_coords, None)


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
            _, nc, n = board.into(nc, delta)

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
        n = cls()
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
        s = cls()
        s.signal = cls.serialized_glyphs.index(glyph)
        return s

    def serialize(self):
        return self.serialized_glyphs[self.output()]

    def output(self):
        return self.signal

    def recalculate_io(self, my_coord, board):
        neighbour_nodes = board.neighbour_objs_into(my_coord)
        for output in neighbour_nodes:
            # Attempt to notify the output space (Not all nodes have inputs, or
            # there may be nothing there)
            try:
                output.inputs.add(self)
            except AttributeError:
                pass

    def toggle(self, value=None):
        """Toggles the signal of the switch, or sets its signal directly."""
        if value is None:
            self.signal = not self.signal
        else:
            self.signal = value


class Portal(SimNode):
    def __init__(self):
        # Portals belong to zero or one portal groups, which are addressed with
        # a single integer.
        # Portals belonging to the same group act like the same piece of wire.
        self.portal_group = None

    @classmethod
    def deserialize(cls, glyph):
        assert(glyph == 'P')
        return cls()
