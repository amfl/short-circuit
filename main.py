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

    def __init__(self):
        super().__init__()
        self.state = False
        self.new_state = False

    def get_output(self) -> bool:
        return self.state

    def calculate_new_state(self):
        self.new_state = any(x.get_output() for x in self.inputs)

    def tick(self):
        self.state = self.new_state

class Nand(SimNode):

    def __init__(self):
        super().__init__()
        self.state = False
        self.new_state = False

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

def main():
    # Make a few wires and connect them to each other
    # Typically this will not be possible
    nodes = [Wire(), Nand(), Wire(), Wire(), Wire()]
    for i in range(len(nodes) - 1):
        nodes[i+1].inputs = [nodes[i]]

    wireWorld = World(nodes)
    print(textwrap.dedent("""
        Wire World

        Standard wires propagate signal one per tick
        """))
    for x in range(4):
        wireWorld.print()
        wireWorld.sim()
        print('----')

    # Make a Nand gate, connect it to itself via a wire
    nodes = [Wire(), Nand()]
    nodes[0].inputs = [nodes[1]]
    nodes[1].inputs = [nodes[0]]

    clockWorld = World(nodes)
    print(textwrap.dedent("""
        Clock World

        Two-tick clock due to wire caching state.
        """))
    for x in range(6):
        clockWorld.print()
        clockWorld.sim()
        print('----')

    # Make a Nand gate, connect it to itself via a instawire
    nodes = [InstaWire(), Nand()]
    nodes[0].inputs = [nodes[1]]
    nodes[1].inputs = [nodes[0]]

    instaclockWorld = World(nodes)
    print(textwrap.dedent("""
        Instaclock World

        The instantaneous wire allows us to produce a one-tick clock.
        """))
    for x in range(6):
        instaclockWorld.print()
        instaclockWorld.sim()
        print('----')

if __name__ == '__main__':
    main()
