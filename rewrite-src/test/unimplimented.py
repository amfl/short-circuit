import unittest
from shortcircuit import Board


@unittest.skip("Bridging wire is unimplemented")
class BridgeTest(unittest.TestCase):
    """Wires will need to cross each other!"""

    def setUp(self):
        board_str = (".--l..\n"
                     "...-..\n"
                     "-r-|--\n"
                     "...-..\n")
        self.board = Board.deserialize(board_str)
        self.top_nand = self.board.get((3, 0))
        self.right_wire = self.board.get((5, 2))
        self.bridge = self.board.get((3, 2))

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
    #     """It makes no sense to ask the bridge what its output is... It has
    #     two signals."""
    #     self.assertIsNone(self.bridge.output())


@unittest.skip("Board copy operations are unimplemented")
class CopyTest(unittest.TestCase):
    """Copying pieces of the board"""
    def setUp(self):
        board_str = ("--...-\n"
                     "d....-\n"
                     "--...-\n")
        self.board = Board.deserialize(board_str)

        self.board.copy((0, 0), (1, 2), (3, 0))

    def testCopy(self):
        copied_str = ("--.---\n"
                      "d..d.-\n"
                      "--.---\n")
        self.assertEqual(self.board.serialize(), copied_str)

    def testIO(self):
        wire = self.board.get((5, 1))
        nand = self.board.get((3, 1))
        self.assertEqual(nand.inputs, {wire})
        self.assertEqual(wire.inputs, {nand})

    def testE2E(self):
        nand = self.board.get((3, 1))
        for i in range(10):
            self.assertEqual(nand.output(), bool(i))
            self.board.tick()


if __name__ == '__main__':
    unittest.main()
