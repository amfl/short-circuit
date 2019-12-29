from datetime import datetime
import logging
import sys

from blessed import Terminal
from blessed.keyboard import Keystroke

import shortcircuit.util as util
from shortcircuit.simnode import Nand, Wire, WireBridge, Switch

logger = logging.getLogger()


class TermUI:
    def __init__(self, args, world):
        self.args = args
        self.t = Terminal()
        self.world = world
        self.cursor_pos = (0, 0)

    def start(self):
        """Start the UI and block until the UI is closed."""

        # Ready the screen for drawing
        print(self.t.enter_fullscreen())

        # Handle input immediately
        with self.t.cbreak():

            # Enter the main game loop
            self.editor_loop()

        print(self.t.exit_fullscreen())

    def _get_fancy_glyph(self, board, coords, node):
        """Gets a fancy glyph for a SimNode. Takes neighbours into account."""
        if isinstance(node, Wire):
            # 4-bit indexed based on neighbours.
            wire_glyphs = [
                'o', '╸', '╺', '━',
                '╹', '┛', '┗', '┻',
                '╻', '┓', '┏', '┳',
                '┃', '┫', '┣', '╋'
            ]

            connecting_neighbour = [board.get(c) is not None
                                    for c in util.neighbour_coords(coords)]
            index = (1 * connecting_neighbour[3] +
                     2 * connecting_neighbour[1] +
                     4 * connecting_neighbour[0] +
                     8 * connecting_neighbour[2])
            return wire_glyphs[index]
        elif isinstance(node, WireBridge):
            # Other possibilities:
            # ['┇', '╏']
            return '┋'
        else:
            return node.serialize()

    def render(self, board):
        """Renders a board onto the current terminal"""
        print(self.t.clear())
        print(self.t.move(0, 0), end='')

        board = self.world.boards[0]

        # DEBUG For super ghetto rendering...
        # print(board.serialize())

        # Colors to use for dead/alive signal
        colors = [8, 1]
        for y in range(len(board.grid)):
            for x in range(len(board.grid[y])):
                coords = (x, y)
                node = board.get(coords)
                try:
                    if self.args.box_draw:
                        glyph = self._get_fancy_glyph(board, coords, node)
                    else:
                        glyph = node.serialize()
                    glyph = self.t.color(colors[node.output()])(glyph)
                except AttributeError:
                    glyph = '.'
                print(glyph, end='')
            print('')

        # Move the cursor to the cursor position
        # Can change this to be smarter if we ever have a viewport
        print(self.t.move(self.cursor_pos[1], self.cursor_pos[0]), end='')
        sys.stdout.flush()

    def _obj_under_cursor(self):
        return self.world.boards[0].get(self.cursor_pos)

    def write_board_to_disk(self, board, filepath):
        logging.info(f'Writing filepath: {filepath}')
        with open(filepath, 'w') as f:
            f.write(board.serialize())

    def key_to_event(self, inp: Keystroke):
        """Convert a keypress + UI state into an event we can put on the UI
        queue"""

        # Check to see if we are modifying the UI state first
        if inp == 'k' or inp.name == 'KEY_UP':
            return {'move': (0, -1)}
        elif inp == 'j' or inp.name == 'KEY_DOWN':
            return {'move': (0, 1)}
        elif inp == 'h' or inp.name == 'KEY_LEFT':
            return {'move': (-1, 0)}
        elif inp == 'l' or inp.name == 'KEY_RIGHT':
            return {'move': (1, 0)}
        elif inp == 'q':
            return {'quit': True}
        elif inp == '.':
            return {'tick': True}
        elif inp == ' ':  # Wire / delete
            node = '-' if self._obj_under_cursor() is None else '.'
            return {'tile_set': {'coord': self.cursor_pos,
                                 'index': 0,
                                 'node': node}}
        elif inp == 'n':
            n = self._obj_under_cursor()
            if isinstance(n, Nand):
                return {'nand_rotate': {'coord': self.cursor_pos,
                                        'index': 0,
                                        'delta': 1}}
            else:
                return {'tile_set': {'coord': self.cursor_pos,
                                     'index': 0,
                                     'node': 'd'}}
        elif inp == 'o':  # Switch
            n = self._obj_under_cursor()
            if isinstance(n, Switch):
                return {'switch_toggle': {'coord': self.cursor_pos,
                                          'index': 0,
                                          'value': None}}
            else:
                return {'tile_set': {'coord': self.cursor_pos,
                                     'index': 0,
                                     'node': 'o'}}
        elif inp == 'b':  # WireBridge
            return {'tile_set': {'coord': self.cursor_pos,
                                 'index': 0,
                                 'node': '|'}}

        elif inp == 'x':  # Examine tile under cursor
            logger.info(repr(self._obj_under_cursor()))

        elif inp == 'w':
            filename = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            return {'write_board': {'index': 0,
                                    'filepath': f'output/{filename}.ssboard'}}

        else:
            return None

    def editor_loop(self):
        while True:
            # Just render the first board for now
            self.render(self.world.boards[0])

            # Get input
            inp = self.t.inkey()
            logger.debug('Key Input: ' + repr(inp))

            ui_event = self.key_to_event(inp)
            if ui_event is None:
                continue

            move_delta = ui_event.get('move')
            quit = ui_event.get('quit')
            write_board = ui_event.get('write_board')

            if move_delta:
                new_pos = util.add(self.cursor_pos, move_delta)
                if min(new_pos) >= 0:
                    self.cursor_pos = new_pos
            elif quit:
                return
            elif write_board:
                index = write_board['index']
                self.write_board_to_disk(self.world.boards[index],
                                         write_board['filepath'])

            else:
                # Pass it along to the world message queue
                self.world.submit(ui_event)
                self.world.process_queue()
