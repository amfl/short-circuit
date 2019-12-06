import logging
import unittest
from shortcircuit import Board, Switch, Nand, Wire

class TestWireJoin(unittest.TestCase):
    def setUp(self):
        board_str = ("-R-.-")
        self.board = Board.deserialize(board_str)

        self.nand = self.board.get((1,0))

        # Join the two wires
        self.new_wire = Wire()
        self.board.set((3,0), self.new_wire)
        self.placed_wire = self.board.get((3,0))

    def testSetPlacesWire(self):
        self.assertIsInstance(self.placed_wire, Wire)

    def testSetPlacesPassedWire(self):
        self.assertIs(self.new_wire, self.placed_wire)

    def testJoinedWiresAreSameObject(self):
        self.assertIs(self.board.get((2,0)), self.board.get((3,0)))
        self.assertIs(self.board.get((4,0)), self.board.get((3,0)))

    def testIOIsUpdated(self):
        output_wire = self.board.get((2,0))
        self.assertIs(list(output_wire.inputs)[0], self.nand)

    def testSoftE2E(self):
        """The end wire should be on after a tick."""
        self.board.tick()
        self.testE2E()

    def testE2E(self):
        """The end wire should be on."""
        final_wire = self.board.get((4,0))
        self.assertTrue(final_wire.output())


if __name__ == '__main__':
    unittest.main()
