import json

class SimNode:
    def __init__(self):
        self.inputs = []
        self.state = False
        self.new_state = False

    def get_output(self) -> bool:
        return self.state

    def calculate_new_state(self):
        """
        Figures out what the new state will be once we tick
        """
        pass

    def tick(self):
        """
        Updates the current state to the new state
        """
        self.state = self.new_state

    def __repr__(self):
        return json.dumps({
            self.__class__.__name__: hex(id(self)),
            "state": self.state,
            "in": [hex(id(x)) for x in self.inputs],
        })

class Wire(SimNode):

    def calculate_new_state(self):
        self.new_state = any(x.get_output() for x in self.inputs)

class Nand(SimNode):

    def calculate_new_state(self):
        self.new_state = not all(x.get_output() for x in self.inputs)

class World:
    def __init__(self, nodelist):
        self.nodes = nodelist
    def print(self):
        for node in self.nodes:
            print(node)
    def sim(self):
        for node in self.nodes:
            node.calculate_new_state()
        for node in self.nodes:
            node.tick()

def main():
    # Make a few wires and connect them to each other
    # Typically this will not be possible
    nodes = [Wire(), Wire(), Wire()]
    nodes[0].inputs = [nodes[1]]
    nodes[1].inputs = [nodes[2]]
    nodes[2].state = True

    wireWorld = World(nodes)
    print('Wire world')
    for x in range(2):
        wireWorld.print()
        wireWorld.sim()
        print('----')

    # Make a Nand gate, connect it to itself via a wire
    nodes = [Wire(), Nand()]
    nodes[0].inputs = [nodes[1]]
    nodes[1].inputs = [nodes[0]]

    clockWorld = World(nodes)
    print('Clock world')
    for x in range(10):
        clockWorld.print()
        clockWorld.sim()
        print('----')

if __name__ == '__main__':
    main()
