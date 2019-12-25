import unittest
from world import World
from shortcircuit import Board, Wire


class TestMessageQueue(unittest.TestCase):
    def setUp(self):
        board_str = ("r--\n"
                     "-.-\n"
                     "---\n")
        self.board = Board.deserialize(board_str)
        self.world = World([self.board])

    def testSetTile(self):
        coord = (0, 0)
        self.world.submit({'tile_set': { 'coord': coord,
                                         'index': 0,
                                         'node': '-' }})
        self.world.process_queue()
        self.assertIsInstance(self.board.get(coord), Wire)

    def testRotateNand(self):
        coord = (0, 0)
        nand = self.board.get(coord)
        self.world.submit({'nand_rotate': { 'coord': coord,
                                            'index': 0,
                                            'delta': 1 }})
        self.world.process_queue()
        self.assertEqual(self.board.get(coord).serialize(), 'd')

    def testTick(self):
        self.world.submit({'tick': True})
        self.world.process_queue()
        nand = self.board.get((0, 0))
        self.assertTrue(nand.output())


if __name__ == '__main__':
    unittest.main()
