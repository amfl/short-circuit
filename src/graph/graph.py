import json
import textwrap

class SimNode:
    def __init__(self):
        self.inputs = []

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
        self.facing = facing

    def get_output(self) -> bool:
        return self.state

    def calculate_new_state(self):
        self.new_state = not all(x.get_output() for x in self.inputs)

    def tick(self):
        self.state = self.new_state

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
            print(node)

    def sim(self):
        """
        Advance the simulation.
        """
        for node in self.nodes:
            node.calculate_new_state()
        for node in self.nodes:
            node.tick()
