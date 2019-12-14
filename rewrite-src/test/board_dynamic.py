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


class TestWireBreak(unittest.TestCase):
    def setUp(self):
        board_str = ("-R---")
        self.board = Board.deserialize(board_str)

        self.nand = self.board.get((1, 0))

        # Split the wire
        self.board.set((3, 0), None)

    def testRemoval(self):
        """The `set` function should be able to delete wire"""
        self.assertIsNone(self.board.get((3, 0)))

    def testSplitWiresAreDifferentObjects(self):
        self.assertIsNot(self.board.get((2, 0)), self.board.get((4, 0)))

    def testIOIsUpdated(self):
        output_wire = self.board.get((2, 0))
        self.assertIs(list(output_wire.inputs)[0], self.nand)

        orphaned_wire = self.board.get((4, 0))
        self.assertEqual(len(orphaned_wire.inputs), 0)

    def testSoftWireSignal(self):
        """The wire groups should have the right outputs after a tick."""
        self.board.tick()
        self.testE2E()

    def testE2E(self):
        """The wire groups should have the right outputs after the break."""
        output_wire = self.board.get((2, 0))
        self.assertTrue(output_wire.output())

        orphaned_wire = self.board.get((4, 0))
        self.assertFalse(orphaned_wire.output())


class TestWireBreakAdvanced(unittest.TestCase):
    def setUp(self):
        board_str = ("r-...-l\n"
                     "r-----l\n"
                     "l-...-r\n")
        self.board = Board.deserialize(board_str)
        self.center_coords = (3, 1)

        self.left_input_nands = {self.board.get((0, 0)),
                                 self.board.get((0, 1))}
        self.left_output_nand = self.board.get((0, 2))

        self.right_input_nands = {self.board.get((6, 0)),
                                  self.board.get((6, 1))}
        self.right_output_nand = self.board.get((6, 2))

    def testBasicAssumptions(self):
        center_wire = self.board.get(self.center_coords)
        self.assertIsInstance(center_wire, Wire)
        self.assertEqual(len(center_wire.inputs), 4)

        self.assertEqual(self.left_output_nand.inputs, {center_wire})
        self.assertEqual(self.right_output_nand.inputs, {center_wire})

    def testWireBreakInputs(self):
        self.board.set(self.center_coords, None)

        left_wire = self.board.get((2, 1))
        right_wire = self.board.get((4, 1))
        self.assertEqual(left_wire.inputs, self.left_input_nands)
        self.assertEqual(right_wire.inputs, self.right_input_nands)

    def testWireBreakOutputs(self):
        self.board.set(self.center_coords, None)

        left_wire = self.board.get((2, 1))
        right_wire = self.board.get((4, 1))
        self.assertEqual(self.left_output_nand.inputs, {left_wire})
        self.assertEqual(self.right_output_nand.inputs, {right_wire})


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
        self.assertEqual(final_wire.inputs, {self.nand})


if __name__ == '__main__':
    unittest.main()
