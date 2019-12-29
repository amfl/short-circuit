import unittest
from shortcircuit.board import Board


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
