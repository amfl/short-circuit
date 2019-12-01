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

class DeserializationTest(unittest.TestCase):
    def setUp(self):
        stuff = ("--udlr\n"
                 "--UDLR\n"
                 "--xo--\n")
        self.board = Board.deserialize(stuff)
    def testWire(self):
        w = self.board.get((0,0))
        self.assertIsInstance(w, Wire)
    def testNands(self):
        # TODO Implement me
        self.assertTrue(False)
    def testSwitches(self):
        switches = [ self.board.get((2,2)),
                     self.board.get((3,2)) ]
        for switch in switches:
            self.assertIsInstance(switch, Switch)

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
