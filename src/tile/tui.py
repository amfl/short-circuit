import logging
import sys

from blessed import Terminal
from blessed.formatters import FormattingString
from blessed.keyboard import Keystroke

logger = logging.getLogger()

class TermUI:
    def handle_inputs(self, inp: Keystroke):
        if inp in 'q' or inp.name == 'KEY_ESCAPE':
            return {'exit': True}

        if inp in 'wk':
            return {'move': (0,-1)}
        elif inp in 'sj':
            return {'move': (0,1)}
        elif inp in 'ah':
            return {'move': (-1,0)}
        elif inp in 'dl':
            return {'move': (1,0)}
        else:
            return {'no_op': True}

    def __init__(self):
        self.t = Terminal()
        self.cursor_pos = (0,0)

        logger.info("----------------------------------")
        logger.info("Terminal colors: %d", self.t.number_of_colors)
        logger.info("Terminal size: %dx%d", self.t.width, self.t.height)

    def editor_loop(self):
        print('Placeholder for Terminal UI')
        print('Press Q to quit')
        while True:
            self.render()

            # Get input
            inp = self.t.inkey()
            logger.debug('Key Input: ' + repr(inp))

            action = self.handle_inputs(inp)

            move = action.get('move')
            if action.get('exit'):
                break
            elif move:
                self.cursor_pos = (
                    self.cursor_pos[0] + move[0],
                    self.cursor_pos[1] + move[1],
                )
                logger.debug('Cursor pos: %s', self.cursor_pos)


    def render(self):
        # Can change this to be smarter if we ever have a viewport
        print(self.t.move(self.cursor_pos[1], self.cursor_pos[0]), end='')
        sys.stdout.flush()

    def start(self):
        # Ready the screen for drawing
        print(self.t.enter_fullscreen())

        # Handle input immediately
        with self.t.cbreak():

            # Enter the main game loop
            self.editor_loop()

        print(self.t.exit_fullscreen())
