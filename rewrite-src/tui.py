import logging
import sys

import util
from world import World
from shortcircuit import Wire

from blessed import Terminal
from blessed.formatters import FormattingString
from blessed.keyboard import Keystroke

logger = logging.getLogger()

class TermUI:
    def __init__(self, args, world):
        self.args = args
        self.t = Terminal()
        self.world = world
        self.cursor_pos = (0,0)

    def start(self):
        """Start the UI and block until the UI is closed."""

        # Ready the screen for drawing
        print(self.t.enter_fullscreen())

        # Handle input immediately
        with self.t.cbreak():

            # Enter the main game loop
            self.editor_loop()

        print(self.t.exit_fullscreen())

    def render(self, board):
        """Renders a board onto the current terminal"""
        print(self.t.clear())
        print(self.t.move(0, 0), end='')

        string = board.serialize()
        print(string)

        # Move the cursor to the cursor position
        # Can change this to be smarter if we ever have a viewport
        print(self.t.move(self.cursor_pos[1], self.cursor_pos[0]), end='')
        sys.stdout.flush()

    def key_to_event(self, inp):
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
            existing_obj = self.world.boards[0].get(self.cursor_pos)
            node = '.' if isinstance(existing_obj, Wire) else '-'
            return {'tile_set': { 'coord': self.cursor_pos,
                                  'index': 0,
                                  'node': node }}
        elif inp == 'n':
            return {'tile_set': { 'coord': self.cursor_pos,
                                  'index': 0,
                                  'node': 'd' }}
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

            if move_delta:
                new_pos = util.add(self.cursor_pos, move_delta)
                if min(new_pos) >= 0:
                    self.cursor_pos = new_pos
            elif quit:
                return

            else:
                # Pass it along to the world message queue
                self.world.submit(ui_event)
                self.world.process_queue()
