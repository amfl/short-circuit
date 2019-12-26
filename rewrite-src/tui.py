import logging
import sys
from datetime import datetime

import util
from shortcircuit import Nand

from blessed import Terminal
from blessed.keyboard import Keystroke

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

    def render_basic(self, board):
        string = board.serialize()
        print(string)

    def render_pretty(self, board):
        # Colors to use for dead/alive signal
        colors = [8, 1]
        for row in board.grid:
            for n in row:
                try:
                    glyph = n.serialize()
                    glyph = self.t.color(colors[n.output()])(glyph)
                except AttributeError:
                    glyph = '.'
                print(glyph, end='')
            print('')

    def render(self, board):
        """Renders a board onto the current terminal"""
        print(self.t.clear())
        print(self.t.move(0, 0), end='')

        if self.args.box_draw:
            self.render_pretty(self.world.boards[0])
        else:
            self.render_basic(self.world.boards[0])

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
        elif inp == ' ':
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
        elif inp == 'x':
            # Examine tile under cursor
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
