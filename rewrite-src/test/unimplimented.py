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


if __name__ == '__main__':
    unittest.main()
