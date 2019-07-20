import logging
import sys

from blessed import Terminal
from blessed.formatters import FormattingString

logger = logging.getLogger()

class TermUI:
    def __init__(self):
        self.t = Terminal()

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

            if inp == 'q':
                break

    def render(self):
        sys.stdout.flush()

    def start(self):
        # Ready the screen for drawing
        print(self.t.enter_fullscreen())

        # Handle input immediately
        with self.t.cbreak():

            # Enter the main game loop
            self.editor_loop()

        print(self.t.exit_fullscreen())
