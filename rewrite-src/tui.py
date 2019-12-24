import logging

from ui import UI

from blessed import Terminal
from blessed.formatters import FormattingString
from blessed.keyboard import Keystroke

logger = logging.getLogger()

class TermUI(UI):
    def __init__(self, args, board):
        super().__init__()

        self.args = args
        self.t = Terminal()
        self.board = board
        self.cursor_pos = (0,0)

    def start(self):
        """Start the UI and block until the UI is closed."""

        super().start()

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

    @classmethod
    def key_to_event(cls, keycode):
        """Convert a keypress + UI state into an event we can put on the UI
        queue"""

        return None

    def editor_loop(self):
        while True:
            self.render(self.board)

            # Get input
            inp = self.t.inkey()
            logger.debug('Key Input: ' + repr(inp))
