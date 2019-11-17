import logging
import json
import textwrap

logger = logging.getLogger()

class SimNode:
    def __init__(self):
        self.inputs = set()

    def get_output(self) -> bool:
        """
        The output of this SimNode
        """
        return True

    def calculate_new_state(self):
        """
        Figures out what the new state will be once we tick
        """
        pass

    def tick(self):
        """
        Updates the current state to the new state
        """
        pass

    def __repr__(self):
        return json.dumps({
            self.__class__.__name__: hex(id(self)),
            "out": self.get_output(),
            "in": [hex(id(x)) for x in self.inputs],
        })

class InstaWire(SimNode):

    def get_output(self) -> bool:
        # InstaWire does not cache state
        # Funny things might happen if `get_output` is not deterministic
        # Infinite loops if InstaWire connects to itself
        assert (not any(filter(lambda i: isinstance(i, InstaWire), self.inputs))), 'Instawire must never connect with itself.'
        return any(x.get_output() for x in self.inputs)

class Wire(SimNode):
    next_available_label = 0

    def __init__(self):
        super().__init__()
        self.state = False
        self.new_state = False
        # For finding connected components

        self.label = Wire.next_available_label
        Wire.next_available_label += 1

    def __str__(self):
        """Used for serialization"""
        return '+'

    def get_output(self) -> bool:
        return self.state

    def calculate_new_state(self):
        self.new_state = any(x.get_output() for x in self.inputs)

    def tick(self):
        self.state = self.new_state

    def __repr__(self):
        return json.dumps({
            self.__class__.__name__: hex(id(self)),
            "out": self.get_output(),
            "in": [hex(id(x)) for x in self.inputs],
            "label": self.label
        })

class Nand(SimNode):

    def __init__(self, facing=0):
        super().__init__()
        self.state = False
        self.new_state = False
        self.facing = 0
        self.set_facing(facing)
        self.serialized = ['u', 'r', 'd', 'l']

    def __str__(self):
        """Used for serialization"""
        glyph = self.serialized[self.facing]
        if self.get_output():
            glyph = glyph.upper()
        return glyph

    def deserialize(self, glyph):
        self.state = glyph.isupper()
        self.set_facing(self.serialized.index(glyph.lower()))

    def get_output(self) -> bool:
        return self.state

    def calculate_new_state(self):
        logger.debug(f'Nand Inputs: {self.inputs}')
        outputs = [x.get_output() for x in self.inputs]
        logger.debug(f'Outputs: {outputs}')
        self.new_state = not all(outputs)

    def tick(self):
        self.state = self.new_state
        logger.info(f'Set my new state: {self.state}')

    def rotate_facing(self, delta):
        self.facing = (self.facing + delta) % 4

    def set_facing(self, facing):
        self.facing = facing

    def get_facing_delta(self):
        facing_list = [
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, 0),
        ]
        return facing_list[self.facing]

class Switch(SimNode):

    def __init__(self, initial_state=False):
        super().__init__()
        self.state = initial_state
        self.new_state = initial_state
        self.serialized = ['x', 'o']

    def __str__(self):
        """Used for serialization"""
        return self.serialized[self.get_output()]

    def deserialize(self, glyph):
        # This can throw ValueError
        self.state = self.serialized.index(glyph)

    def get_output(self) -> bool:
        return self.state

    def set_state(self, new_state: bool):
        self.state = new_state

    def toggle(self):
        self.state = not self.state

class World:
    """
    Simply a holder for our nodes.
    """

    def __init__(self, nodelist):
        self.nodes = nodelist

    def print(self):
        """
        Pretty-print all the nodes for debugging.
        """
        for node in self.nodes:
            print(repr(node))

    def sim(self):
        """
        Advance the simulation.
        """
        for node in self.nodes:
            node.calculate_new_state()
        for node in self.nodes:
            node.tick()
