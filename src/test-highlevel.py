import logging
import unittest
from highlevel import Board, Switch, Nand, Wire

class TestTest(unittest.TestCase):
    def testThings(self):
        self.assertEqual(True, True)

class FromScratchTest(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.initialize_grid((10,10))
    def testBasicGet(self):
        self.assertIsNone(self.board.get((3,3)))

class SerdeTest(unittest.TestCase):
    def setUp(self):
        self.board_str = ("--udlr\n"
                          "--UDLR\n"
                          "U-xo--\n")
        self.board = Board.deserialize(self.board_str)

    def testWireDeserialization(self):
        w = self.board.get((0,0))
        self.assertIsInstance(w, Wire)

    def testWireDeserializationState(self):
        """With no ticking, the output wire should already be on, because the bottom left NAND is outputting to it."""

        w = self.board.get((0,0))
        self.assertTrue(w.output())

    def testNandDeserialization(self):
        unpowered_nands = [(2,0), (3,0), (4,0), (5,0)]
        powered_nands   = [(2,1), (3,1), (4,1), (5,1)]
        unpowered_nands = list(map(lambda x: self.board.get(x), unpowered_nands))
        powered_nands = list(map(lambda x: self.board.get(x), powered_nands))
        for x in powered_nands:
            self.assertIsInstance(x, Nand)
            self.assertTrue(x.output())
        for x in unpowered_nands:
            self.assertIsInstance(x, Nand)
            self.assertFalse(x.output())

    def testSwitchDeserialization(self):
        switches = [ self.board.get((2,2)),
                     self.board.get((3,2)) ]
        for switch in switches:
            self.assertIsInstance(switch, Switch)

    def testSerdeE2E(self):
        """Deserializing and reserializing should result in the same string"""
        board_str = self.board.serialize()
        self.assertEqual(self.board_str, board_str)

    def testWireGroups(self):
        # Take two wires from the left group
        left_wires = [ self.board.get((0,0)),
                       self.board.get((1,2)) ]

        # Take two wires from the right group
        right_wires = [ self.board.get((4,2)),
                        self.board.get((5,2)) ]

        self.assertEqual(left_wires[0], left_wires[1])
        self.assertEqual(right_wires[0], right_wires[1])
        self.assertNotEqual(left_wires[0], right_wires[0])

class IOTest(unittest.TestCase):
    def setUp(self):
        board_str = ("-r-..-\n"
                     "-.-..x\n"
                     "---..-\n")
        self.board = Board.deserialize(board_str)

        self.nand = self.board.get((1,0))
        self.nand_wire = self.board.get((1,2))

        self.switch = self.board.get((5,1))
        self.switch_wires = [ self.board.get((5,0)),
                              self.board.get((5,2)) ]

    def testNandIO(self):
        self.assertEqual(self.nand.inputs, set([self.nand_wire]))
        self.assertEqual(self.nand_wire.inputs, set([self.nand]))

    def testSwitchIO(self):
        for wire in self.switch_wires:
            self.assertEqual(wire.inputs, set([self.switch]))

    def test1TickClock(self):
        """Check a NAND connected to itself forms a 1 tick clock."""
        for i in range(10):
            desired = bool(i % 2)
            self.assertEqual(self.nand_wire.output(), desired)
            self.board.tick()

class BasicTest(unittest.TestCase):
    """Make sure that the output of the NAND turns on after a few ticks. This
    should be true regardless of which ticking mechanism is used."""
    def setUp(self):
        board_str = ("-r--\n")
        self.board = Board.deserialize(board_str)

        self.input_wire = self.board.get((0,0))
        self.nand = self.board.get((1,0))
        self.output_wires = [ self.board.get((2,0)),
                              self.board.get((3,0))  ]

    def testIO(self):
        self.assertIs(list(self.output_wires[0].inputs)[0], self.nand)

    def testBasicTicking(self):
        for i in range(5):
            self.board.tick()

        self.assertFalse(self.input_wire.output())
        self.assertTrue(self.nand.output())
        self.assertTrue(self.output_wires[0].output())

    def testWireGroups(self):
        self.assertIs(self.output_wires[0], self.output_wires[1])

class DirectSimNodeOutputTest(unittest.TestCase):
    """CAUTION: Atm this fails half the time, possibly due to order of set iteration being undefined."""

    def setUp(self):
        board_str = ("-rR-.\n"
                     ".....\n"
                     "-r-R-\n")
        self.board = Board.deserialize(board_str)

        self.input_wires = [ self.board.get((0,0)),
                             self.board.get((0,2)) ]
        self.left_nands = [ self.board.get((1,0)),
                            self.board.get((1,2)) ]
        self.right_nands = [ self.board.get((2,0)),
                             self.board.get((3,2)) ]
        self.output_wires = [ self.board.get((3,0)),
                              self.board.get((4,2)) ]
        self.middle_wire = self.board.get((2, 2))

    def testIO(self):
        """Make sure the top two nands connect directly together"""
        self.assertIs(list(self.right_nands[0].inputs)[0], self.left_nands[0])

    def testTick(self):
        for i in range(5):
            print(self.board.serialize())
            self.assertEqual(self.left_nands[1].output(), self.middle_wire.output())

            self.assertEqual(self.left_nands[0].output(), self.left_nands[1].output())
            self.assertEqual(self.right_nands[0].output(), self.right_nands[1].output())
            self.assertEqual(self.output_wires[0].output(), self.output_wires[1].output())
            self.board.tick()

class AdvancedDirectSimNodeOutputTest(unittest.TestCase):
    def setUp(self):
        nogap = ("--D\n"
                 "u.d\n"
                 "---\n")
        gap   = ("--D\n"
                 "u.-\n"
                 "--l\n")
        self.boards = [
                    Board.deserialize(nogap),
                    Board.deserialize(gap),
                ]
        # Keep track of the leftmost nand on both grids.
        # They should both always have the same value.
        self.nands = list(map(lambda x: x.get((0,1)), self.boards))

    def testOutputToSimNodes(self):
        """
        Make sure that SimNodes can output directly to other SimNodes without
        stuff in between.
        """
        for i in range(10):
            print(f'==={i}===')
            print(self.boards[0].serialize())
            print(self.boards[1].serialize())
            self.assertEqual(self.nands[0].output(), self.nands[1].output())
            self.boards[0].tick()
            self.boards[1].tick()

class BridgeTest(unittest.TestCase):
    """Wires will need to cross each other!"""

    def setUp(self):
        board_str = (".--l..\n"
                     "...-..\n"
                     "-r-|--\n"
                     "...-..\n")
        self.board = Board.deserialize(board_str)
        self.top_nand = self.board.get((3,0))
        self.right_wire = self.board.get((5,2))
        self.bridge = self.board.get((3,2))

        self.board.tick()
        self.board.tick()
        self.board.tick()

    def testBridgeTransmits(self):
        """Ensure signal crosses the bridge when it's supposed to"""
        self.assertTrue(self.right_wire.output())

    def testBridgeDoesNotBleed(self):
        """Make sure signal isn't "bleeding under" the bridge"""
        self.assertTrue(self.top_nand.output())

    # def testBridgeHasNoOutput(self):
    #     """It makes no sense to ask the bridge what its output is... It has two signals."""
    #     self.assertIsNone(self.bridge.output())

if __name__ == '__main__':
    unittest.main()
