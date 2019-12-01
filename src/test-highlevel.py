import logging
import unittest
from highlevel import Board, Switch, Nand, Wire

class TestTest(unittest.TestCase):
    def testThings(self):
        self.assertEqual(True, True)

class FromScratchTest(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.initialize_grid((10,10))
    def testBasicGet(self):
        self.assertIsNone(self.board.get((3,3)))

class SerdeTest(unittest.TestCase):
    def setUp(self):
        self.board_str = ("--udlr\n"
                          "--UDLR\n"
                          "--xo--\n")
        self.board = Board.deserialize(self.board_str)
    def testWireDeserialization(self):
        w = self.board.get((0,0))
        self.assertIsInstance(w, Wire)
    def testNandDeserialization(self):
        unpowered_nands = [(2,0), (3,0), (4,0), (5,0)]
        powered_nands   = [(2,1), (3,1), (4,1), (5,1)]
        unpowered_nands = list(map(lambda x: self.board.get(x), unpowered_nands))
        powered_nands = list(map(lambda x: self.board.get(x), powered_nands))
        for x in powered_nands:
            self.assertIsInstance(x, Nand)
            self.assertTrue(x.output())
        for x in unpowered_nands:
            self.assertIsInstance(x, Nand)
            self.assertFalse(x.output())

    def testSwitchDeserialization(self):
        switches = [ self.board.get((2,2)),
                     self.board.get((3,2)) ]
        for switch in switches:
            self.assertIsInstance(switch, Switch)

    def testSerdeE2E(self):
        """Deserializing and reserializing should result in the same string"""
        board_str = self.board.serialize()
        self.assertEqual(self.board_str, board_str)

class BasicTest(unittest.TestCase):
    """Make sure that the output of the NAND turns on after a few ticks. This
    should be true regardless of which ticking mechanism is used."""
    def setUp(self):
        gridStr = ("-r--\n")
        self.board = Board.deserialize(gridStr)

    def runTest(self, mechanism):
        logging.debug(f'Testing mechanism: {mechanism}')
        for i in range(5):
            self.board.tick(mechanism)

        outputWire = self.board.get((3,0))
        self.assertTrue(outputWire.get_output())

    def testMechansimA(self):
        self.runTest('a')

    def testMechansimB(self):
        self.runTest('b')

class DirectSimNodeOutputTest(unittest.TestCase):
    def setUp(self):
        nogap = ("--D\n"
                 "u.d\n"
                 "---\n")
        gap   = ("--D\n"
                 "u.-\n"
                 "--l\n")
        self.boards = [
                    Board.deserialize(nogap),
                    Board.deserialize(gap),
                ]
        self.sampleNands = list(map(lambda x: x.get((0,1)), self.boards))

    def testOutputToSimNodes(self):
        """
        Make sure that SimNodes can output directly to other SimNodes without
        stuff in between.
        """
        print(self.sampleNands)
        for i in range(10):
            self.boards[0].tick('b')
            self.boards[1].tick('a')
            print(self.sampleNands[1].get_output())
            self.assertTrue(
                    self.sampleNands[0].get_output(),
                    self.sampleNands[1].get_output())

if __name__ == '__main__':
    unittest.main()
