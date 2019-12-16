import argparse
from shortcircuit import Board

import logging
logger = logging.getLogger()
logname = 'output/gameplay.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format=('%(asctime)s,%(msecs)d %(module)s '
                            '%(levelno)s %(message)s'),
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


def main():

    parser = argparse.ArgumentParser(description='Tile-based digital logic '
                                                 'sandbox')
    parser.add_argument('--file',
                        help='Load state from file')
    parser.add_argument('-x', '--width', dest='width', metavar='N',
                        type=int, default=10, help='Width of the board')
    parser.add_argument('-y', '--height', dest='height', metavar='N',
                        type=int, default=10, help='Height of the board')

    box_parser = parser.add_mutually_exclusive_group(required=False)
    box_parser.add_argument('--box-draw', dest='box_draw', action='store_true',
                            help='Enable UTF-8 box drawing characters')
    box_parser.add_argument('--no-box-draw', dest='box_draw',
                            action='store_false',
                            help='Disable UTF-8 box drawing characters')
    box_parser.set_defaults(box_draw=True)

    args = parser.parse_args()

    logger.debug(args)

    if args.file:
        # Read board from file
        with open(args.file, 'r') as f:
            board_str = f.read()
            board = Board.deserialize(board_str)
    else:
        # Create a new board
        board = Board()
        board.initialize_grid((args.width, args.height))

    # # Start up the UI
    # t = TermUI(args, g)
    # # Block until we quit the UI
    # t.start()


if __name__ == '__main__':
    main()
