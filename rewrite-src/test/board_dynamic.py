import unittest
from shortcircuit import Board, Wire


class TestWireJoin(unittest.TestCase):
    def setUp(self):
        board_str = ("-R-.-")
        self.board = Board.deserialize(board_str)

        self.nand = self.board.get((1, 0))

        # Join the two wires
        self.new_wire = Wire()
        self.board.set((3, 0), self.new_wire)
        self.placed_wire = self.board.get((3, 0))

    def testSetPlacesWire(self):
        """Passing a wire object should result in a wire object being placed at
        the given coordinates."""
        self.assertIsInstance(self.placed_wire, Wire)

    def testSetPlacesPassedWire(self):
        """The wire which appears on the grid must be the same wire which was
        actually given to the `set` method."""
        self.assertIs(self.new_wire, self.placed_wire)

    def testJoinedWiresAreSameObject(self):
        self.assertIs(self.board.get((2, 0)), self.board.get((3, 0)))
        self.assertIs(self.board.get((4, 0)), self.board.get((3, 0)))

    def testIOIsUpdated(self):
        output_wire = self.board.get((2, 0))
        self.assertIs(list(output_wire.inputs)[0], self.nand)

    def testSoftE2E(self):
        """The end wire should be on after a tick."""
        self.board.tick()
        self.testE2E()

    def testE2E(self):
        """The end wire should be on."""
        final_wire = self.board.get((4, 0))
        self.assertTrue(final_wire.output())


class TestComponentReplacement(unittest.TestCase):
    """Make sure that joining two wire groups via deleting a component doesn't
    leave incorrect IO information around."""
    def setUp(self):
        board_str = ("-R-r-")
        self.board = Board.deserialize(board_str)
        self.board.set((3, 0), Wire())

        self.nand = self.board.get((1, 0))

    def testJoinedWiresAreSameObject(self):
        self.assertIs(self.board.get((2, 0)), self.board.get((3, 0)))
        self.assertIs(self.board.get((4, 0)), self.board.get((3, 0)))

    def testIO(self):
        final_wire = self.board.get((4, 0))
        self.assertEqual(len(final_wire.inputs), 1)
        self.assertIs(list(final_wire.inputs)[0], self.nand)


if __name__ == '__main__':
    unittest.main()
