from graph.graph import *

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
