import unittest
from shortcircuit import Board, Wire, Nand


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

    def testWireReplacementInputs(self):
        new_nand = Nand()
        self.board.set(self.center_coords, new_nand)

        left_wire = self.board.get((2, 1))
        right_wire = self.board.get((4, 1))
        self.assertEqual(left_wire.inputs, self.left_input_nands)
        self.assertEqual(right_wire.inputs, self.right_input_nands)
        self.assertEqual(new_nand.inputs, {left_wire, right_wire})

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


class TestNandRotation(unittest.TestCase):
    """NANDs are directional. Rotating them needs to update connections."""
    def setUp(self):
        self.board = Board.deserialize("R--\n"
                                       "-..\n")
        self.nand = self.board.get((0, 0))
        self.bottom_wire = self.board.get((0, 1))
        self.right_wire = self.board.get((2, 0))

        self.nand.rotate_facing(1, (0, 0), self.board)

    def testFacing(self):
        self.assertEqual(self.nand.serialize(), 'D')

    def testIO(self):
        self.assertEqual(self.right_wire.inputs, set())
        self.assertEqual(self.nand.inputs, {self.right_wire})
        self.assertEqual(self.bottom_wire.inputs, {self.nand})

    def testE2E(self):
        """The outputs should be accurate after a few ticks.

        I am undecided as to what the behavior should be after zero or one
        ticks..."""
        self.board.tick()
        self.board.tick()
        self.assertFalse(self.right_wire.output())
        self.assertTrue(self.bottom_wire.output())


class ClockTest(unittest.TestCase):
    def setUp(self):
        board_str = (".--\n"
                     "d.-\n"
                     ".--\n")
        self.board = Board.deserialize(board_str)
        self.nand = self.board.get((0, 1))

    def testIOInputFirst(self):
        self.board.set((0, 0), Wire())
        self.board.set((0, 2), Wire())

        wire = self.board.get((1, 2))
        self.assertEqual(self.nand.inputs, {wire})
        self.assertEqual(wire.inputs, {self.nand})

    def testIOOutputFirst(self):
        self.board.set((0, 2), Wire())
        self.board.set((0, 0), Wire())

        wire = self.board.get((1, 2))
        self.assertEqual(self.nand.inputs, {wire})
        self.assertEqual(wire.inputs, {self.nand})


class ClockTest2(unittest.TestCase):
    def setUp(self):
        board_str = ("---\n"
                     "d..\n"
                     "---\n")
        self.board = Board.deserialize(board_str)
        self.nand = self.board.get((0, 1))

        # Dynamically finish the loop
        self.board.set((2, 1), Wire())

    def testBasicAssumptions(self):
        top_wire = self.board.get((2, 0))
        bottom_wire = self.board.get((2, 2))
        self.assertIs(top_wire, bottom_wire)
        self.assertEqual(self.nand.inputs, {top_wire})
        self.assertEqual(bottom_wire.inputs, {self.nand})

    def testTickingAfterWireJoin(self):
        for i in range(10):
            self.assertEqual(bool(i % 2), self.nand.output())
            self.board.tick()


class PlaygroundTest(unittest.TestCase):
    """A big board to hold all the miscellaneous test cases"""

    def setUp(self):
        board_str = ("r----r-.-\n"
                     ".-.......\n"
                     "-l-d.....\n"
                     "-..--....\n")
        self.board = Board.deserialize(board_str)

    def testPlaceNand(self):
        coords = (6, 2)
        self.board.set(coords, Nand())
        self.assertIsInstance(self.board.get(coords), Nand)

    def testPlaceNandOnIsolatedWire(self):
        coords = (8, 0)
        self.board.set(coords, Nand())
        self.assertIsInstance(self.board.get(coords), Nand)


if __name__ == '__main__':
    unittest.main()
