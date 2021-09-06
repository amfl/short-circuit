import unittest

import json
import shortcircuit.util as util
from shortcircuit.board import Board
from shortcircuit.simnode import Nand, Wire, Portal


class TestCoordsParse(unittest.TestCase):
    def setUp(self):
        portals = { 'portals': {
            1: [(0,4,1), (0,1,0) ]}}
        board_str = ("-P.d-\n" +
                     "o...P\n" +
                     "\n" +
                     json.dumps(portals))
        self.board = Board.deserialize(board_str)

        self.portal = self.board.get((1, 0))

    def testDeserialize(self):
        self.assertIsInstance(self.portal, Portal)

    def testConnectivity(self):
        """Assert that wire connectivity flows through portals"""

        wireLeft = self.board.get((0,0))
        wireRight = self.board.get((4,0))

        self.assertIs(wireLeft, wireRight)

    def testSignalPropagation(self):
        switch = self.board.get((0,1))
        nand = self.board.get((3,0))

        for i in range(10):
            desired = bool(i % 2)
            self.assertEqual(nand.output(), desired)
            switch.toggle()
            self.board.tick()


if __name__ == '__main__':
    unittest.main()
