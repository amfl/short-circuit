import logging

import shortcircuit.util as util
from shortcircuit.simnode import SimNode, Wire, Nand, Switch

logger = logging.getLogger()


class Board:
    def __init__(self):
        # Multidimensional array
        self.grid = None
        # TODO Do I want a bidict?
        # coord -> SimNode, SimNode -> [coord]
        # Or some kind of horrible bidirectional multimap...
        # https://stackoverflow.com/questions/39624938/need-a-bidirectional-map-which-allows-duplicate-values-and-returns-list-of-valu
        self.node_cache = dict()  # coord -> SimNode
        self.wire_cache = dict()  # Wire -> [coords]

        # coord1 -> wire1
        # coord2 -> wire1
        # coord3 -> node2

        # thus, inversely...

        # wire1 -> coord1, coord2
        # node2 -> coord3

    def initialize_grid(self, dimensions):
        (x, y) = dimensions
        self.grid = [[None] * x for iy in range(y)]

    def tick(self):
        """Ticks the sim. Could work in parallel. Only touches the
        graph_cache."""
        wires, nodes = self._get_caches()
        logger.info(f'TICKING THE SIM')
        logger.debug(f'wires: {wires} nodes: {nodes}')

        for (_, _, node) in nodes:
            logger.debug(f'Ticking the node: {node}')
            node.calculate_next_output()
        # Because nodes can connect directly to other nodes, the tick step must
        # be separate from the calculation step. Otherwise, the unsorted nature
        # of the node set will produce non-deterministic behavior.
        for (_, _, node) in nodes:
            node.tick()
        for wire in wires:
            logger.debug(f'Ticking the wire: {wire}')
            wire.calculate_next_output()
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
        """Places a SimNode on the board. This also performs any wire joining
        and IO updates."""

        old_node = self.get(coords)
        self.set_basic(coords, node)

        if old_node is not None:
            # We need to delete the old node first!
            # Clear it out of our neighbour's inputs.
            for n in self.neighbour_objs(coords):
                n.input_remove(old_node)

        # Perform any required wire joins/breaks
        if isinstance(node, Wire):
            self._grid_local_wire_join(coords, node)
        elif isinstance(old_node, Wire):
            self._grid_local_wire_break(coords, old_node)

        # Make sure all neighbours have their connections updated
        self._grid_local_io_refresh(coords)

    def set_basic(self, coords, node: SimNode):
        # Update the contents of the board with the new object
        x, y = coords
        if x < 0 or y < 0:
            raise IndexError
        self.grid[y][x] = node

    @staticmethod
    def deserialize_simnode(glyph):
        for cls in [Wire, Nand, Switch]:
            try:
                return cls.deserialize(glyph)
            except:
                continue
        return None

    @classmethod
    def deserialize(cls, string):
        """Rebuilds the grid from a string."""

        rows = string.split('\n')

        board = Board()
        board.grid = [list(map(cls.deserialize_simnode, list(row)))
                      for row in rows]

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
                if me is not None:
                    glyph = me.serialize()
                string += glyph
            string += '\n'
        # Slice off the last newline otherwise we end up with two of them
        return string[:-1]

    #####################################################
    # Convenience methods
    #####################################################

    def neighbour_objs(self, coords):
        """Returns the neighbouring nodes (No `None`s)"""
        n_objs = [self.get(c) for c in util.neighbour_coords(coords)]
        return list(filter(None, n_objs))

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

    def _recursive_wire_replace(self, old_wire_coords, new_wire):
        """Recursively flood through a wire and replace it with a new
        wire.

        TODO: How does caching fit into this?

        Returns : set
          Set of all the SimNodes which will need to have their IO updated.

        """
        # Replace the current wire
        self.set_basic(old_wire_coords, new_wire)

        dirty_simnodes = {}

        # In the list of all wire neighbours which aren't the new wire...
        for nc in util.neighbour_coords(old_wire_coords):
            n = self.get(nc)
            if isinstance(n, Wire) and n != new_wire:
                # Replace them, too!
                dirty_simnodes.update(
                        self._recursive_wire_replace(nc, new_wire))
            elif n is not None:
                dirty_simnodes[nc] = n
        return dirty_simnodes

    def _grid_local_wire_join(self, coords, new_wire: Wire):
        """Ensures all wires in the wire group at the given coords consist of
        the same object, and that inputs/outputs are correct.

        Parameters
        ----------
        coords : tuple
            A tuple of grid coordinates to join at.
        new_wire : Wire
            The new wire to replace the entire group with.
        """
        neighbouring_wires = [sn for sn in self.neighbour_objs(coords)
                              if isinstance(sn, Wire)]

        new_wire.signal = any([w.output() for w in neighbouring_wires])

        old_input_sets = [w.inputs for w in neighbouring_wires]
        # The new inputs are a union of all the old input sets
        new_wire.inputs = set().union(*old_input_sets)

        dirty_simnodes = self._recursive_wire_replace(coords, new_wire)

        # Update IO for all dirty_simnodes
        for coord, n in dirty_simnodes.items():
            n.recalculate_io(coord, self)
        # Make sure the new wires immediately show the correct value
        new_wire.calculate_next_output()
        new_wire.tick()

        return new_wire

    def _grid_local_wire_break(self, coords, broken_wire: Wire):
        """Break a wire into multiple bits if required

        Parameters
        ----------

        coords : (x, y)
          Coordinates of where the wire group was broken.
        broken_wire : Wire
          The wire object which was broken.
        """

        current_obj = self.get(coords)
        assert(not isinstance(current_obj, Wire))

        # Note: This can work even if there are no wires... Just marks all the
        #       neighbours as dirty.
        new_wires = set()
        dirty_simnodes = {}  # coord -> obj
        for nc in util.neighbour_coords(coords):
            # Use coords to avoid mutating what we are iterating over
            n = self.get(nc)
            if n is broken_wire:
                new_wire = Wire()
                dirty_simnodes.update(
                        self._recursive_wire_replace(nc, new_wire))
                # Update this later - Can't do here because we need to wait for
                # dirty simnodes to refresh
                new_wires.add(new_wire)
            elif n is not None:
                dirty_simnodes[nc] = n

        # Update IO for all dirty_simnodes
        for coord, n in dirty_simnodes.items():
            n.recalculate_io(coord, self)
        # Make sure the new wires immediately show the correct value
        for wire in new_wires:
            wire.calculate_next_output()
            wire.tick()

    def _grid_local_io_refresh(self, coords):
        """Update IO for myself and my neighbours"""
        area_coords = util.neighbour_coords(coords) + [coords]
        for c in area_coords:
            n = self.get(c)
            if n is not None:
                n.recalculate_io(c, self)

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

                if not isinstance(tile, Wire):
                    continue

                left = tile_lookup.get((x-1, y))
                top = tile_lookup.get((x, y-1))

                neighbouring_labels = [x for x in [left, top] if x is not None]
                try:
                    my_label = min(neighbouring_labels)
                    if len(set(neighbouring_labels)) == 2:
                        connections.add(
                                (my_label, max(neighbouring_labels)))
                except ValueError:
                    # Looks like there are no neighbouring labels, so this is a
                    # new group.
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
            # Beware that this `find` mutates `data`!
            # Must `find` each element once first if you want to operate on the
            # list directly.
            group = find(data, i)

            if i != group:
                label_lookup[group] = label_lookup[group] + label_lookup[i]
                for t in label_lookup[i]:
                    tile_lookup[t] = group
                del label_lookup[i]

        # Component labelling complete!
        # Now we can do what we came here for - Let's replace all the wires so
        # that each group is made up of the same Wire object.
        for label, coords in label_lookup.items():
            logger.debug(f'Wire group: {label} is made from coords: {coords}')
            wire = Wire()
            for (x, y) in coords:
                # Low-level wire replace.
                self.grid[y][x] = wire

    def _grid_global_io_refresh(self):
        wires, nodes = self._get_caches()
        for wire in wires:
            wire.inputs = set()
        for (x, y, node) in nodes:
            node.recalculate_io((x, y), self)

        # Tick all the wires so they are all are up to date
        # Remember wires are direct proxies for the output of their inputs
        for wire in wires:
            wire.calculate_next_output()
            wire.tick()
