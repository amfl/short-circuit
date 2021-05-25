import unittest
from shortcircuit.board import Board


class CopyTest(unittest.TestCase):
    """Copying pieces of the board"""
    def setUp(self):
        board_str = ("--...-\n"
                     "d....-\n"
                     "--...-\n")
        self.board = Board.deserialize(board_str)

        self.board.copy((0, 0), (2, 3), (3, 0))

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
            self.assertEqual(nand.output(), bool(i % 2))
            self.board.tick()

    def testWireConnectivity(self):
        """Copied wires should connect to existing wires if appropriate"""

        wire_copied = self.board.get((4, 0))
        wire_adjacent = self.board.get((5, 0))

        self.assertIs(wire_adjacent, wire_copied)

    def testNandsAreDifferent(self):
        """Copying should not result in duplicated SimNode objects"""

        nand_original = self.board.get((0, 1))
        nand_copied = self.board.get((3, 1))

        self.assertIsNot(nand_original, nand_copied)

    def testWiresAreDifferent(self):
        """Copying should not result in duplicated SimNode objects"""

        wire_original = self.board.get((0, 0))
        wire_copied = self.board.get((4, 0))

        self.assertIsNot(wire_original, wire_copied)


if __name__ == '__main__':
    unittest.main()
