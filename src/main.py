import logging

from graph.proto import *
from tile.tui import *
from tile.grid import Grid
import argparse

logger = logging.getLogger()
logname = 'gameplay.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(module)s %(levelno)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def main():
    # Run the prototype code for graph representation
    # proto()

    parser = argparse.ArgumentParser(description='A Turing complete... Thing.')
    parser.add_argument('-x', '--width', dest='width', metavar='N', type=int, default=10,
                        help='Width of the grid')
    parser.add_argument('-y', '--height', dest='height', metavar='N', type=int, default=10,
                        help='Height of the grid')
    box_parser = parser.add_mutually_exclusive_group(required=False)
    box_parser.add_argument('--box-draw', dest='box_draw', action='store_true',
                            help='Enable UTF-8 box drawing characters')
    box_parser.add_argument('--no-box-draw', dest='box_draw', action='store_false',
                            help='Disable UTF-8 box drawing characters')
    box_parser.set_defaults(box_draw=True)
    args = parser.parse_args()

    logger.debug(args)

    # Create a grid
    g = Grid(args.width, args.height)

    # Start up the UI
    t = TermUI(args, g)
    # Block until we quit the UI
    t.start()

if __name__ == '__main__':
    main()
