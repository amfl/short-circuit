import unittest
from tile.grid import Grid

class TestTest(unittest.TestCase):
    def testThings(self):
        self.assertEqual(True, True)

class BasicTest(unittest.TestCase):
    """Make sure that the output of the NAND turns on after a few ticks. This
    should be true regardless of which ticking mechanism is used."""
    def setUp(self):
        gridStr = ("-r--\n")
        self.grid = Grid.deserialize_from_string(gridStr)
        print('setup done')

    def runTest(self, mechanism):
        for i in range(5):
            self.grid.tick(mechanism)

        outputWire = self.grid.get(3,0)
        self.assertTrue(outputWire.get_output())

    def testMechansimA(self):
        self.runTest('a')

    def testMechansimB(self):
        self.runTest('b')

class TickingTest(unittest.TestCase):
    def setUp(self):
        nogap = ("--D\n"
                 "u.d\n"
                 "---\n")
        gap   = ("--D\n"
                 "u.+\n"
                 "--l\n")
        self.grids = [
                    Grid.deserialize_from_string(nogap),
                    Grid.deserialize_from_string(gap),
                ]
        self.sampleNands = list(map(lambda x: x.get(0,1), self.grids))

    def testOutputToSimNodes(self):
        """
        Make sure that SimNodes can output directly to other SimNodes without
        stuff in between.
        """
        print(self.sampleNands)
        for i in range(10):
            self.grids[0].tick('b')
            self.grids[1].tick('b')
            print(self.sampleNands[1].get_output())
            self.assertTrue(
                    self.sampleNands[0].get_output(),
                    self.sampleNands[1].get_output())

if __name__ == '__main__':
    unittest.main()
