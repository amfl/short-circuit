def SimNode:
    def get_output(self):
        return False

    def calculate_next_output(self):
        pass

class Wire(SimNode):
    pass
    # Thoughts:
    #  - Maintain a list of coords which this wire is comprised of
    #    Then we can refer to it when doing wire splits/joins?
    #  - Maintain a dict of coords -> neighbouring SimNodes as well as (or
    #    instead of) a set of inputs/outputs. Then we can do splits/joins
    #    without ever checking neighbours

class Nand(SimNode):
    pass

class Switch(SimNode):
    pass

def Board:
    def __init__(self):
        self.grid = None
        self.node_cache = set()
        self.wire_cache = set()

    def tick(self):
        """Ticks the sim. Could work in parallel. Only touches the graph_cache."""
        for node in self.node_cache:
            node.tick()
        for wire in self.wire_cache:
            wire.tick()

    def safe_grid_mutate(self, coords, node: SimNode):
        """Places a SimNode on the board. This also performs any wire joining and IO updates."""
        if isinstance(node, Wire):
            self._grid_wire_join(coords, node)
        else:
            self._grid_wire_break(coords, node)

        self._grid_neighbour_io_refresh(coords)

    def deserialize(self, string):
        """Rebuilds the board from a string."""
        pass

    def serialize(self):
        """Dumps current grid state to a string."""
        pass

    #####################################################
    # Internal use methods
    #####################################################

    def _grid_wire_join(self, coords, node: SimNode):
        """Join multiple wires into one if required"""
        pass

    def _grid_wire_break(self, coords):
        """Break a wire into multiple bits if required"""
        pass

    def _grid_neighbour_io_refresh(self, coords):
        pass
