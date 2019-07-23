import logging
import sys
from tile.grid import Grid, Tile

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
        elif inp in ' n':
            return {'toggle': {'direction': 1}}
        elif inp == 'p':
            return {'toggle': {'direction': -1}}
        else:
            return {'no_op': True}

    def __init__(self, grid: Grid):
        self.t = Terminal()
        self.grid = grid
        self.cursor_pos = (0,0)

        # Used for rendering tiles
        self.glyphs = {
            Tile.GROUND: '.',
            Tile.WIRE: '+',
            Tile.NAND_UP: '^',
            Tile.NAND_DOWN: 'v',
            Tile.NAND_LEFT: '<',
            Tile.NAND_RIGHT: '>',
        }

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
            toggle = action.get('toggle')

            if action.get('exit'):
                break
            elif move:
                self.cursor_pos = (
                    self.cursor_pos[0] + move[0],
                    self.cursor_pos[1] + move[1],
                )
                logger.debug('Cursor pos: %s', self.cursor_pos)
            elif toggle:
                # Toggle between tile pieces
                x, y = self.cursor_pos
                current = self.grid.tiles[y][x]
                self.grid.tiles[y][x] = Tile((current.value + toggle['direction']) % len(Tile))

    def render(self):
        # Render the grid
        print(self.t.move(0, 0), end='')
        for y in range(len(self.grid.tiles)):
            for x in range(len(self.grid.tiles[y])):
                # Get the glyph which represents this tile
                glyph = self.glyphs.get(self.grid.tiles[y][x], '?')
                print(glyph, end='')
            print()

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
