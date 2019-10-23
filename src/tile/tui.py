import logging
import sys
from tile.grid import Grid
from graph.graph import Nand, Wire

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
            return {'tile_toggle': {'direction': 1}}
        elif inp == 'p':
            return {'tile_toggle': {'direction': -1}}
        elif inp == 't':
            return {'tile_set': {'tile': 'nand'}}
        elif inp == 'z':
            return {'debug': True}
        else:
            return {'no_op': True}

    def __init__(self, args, grid: Grid):
        self.args = args
        self.t = Terminal()
        self.grid = grid
        self.cursor_pos = (0,0)

        # Used for rendering tiles
        self.glyphs = {
            'ground': '.',
            'wire': '+',
            'nand_up': '^',
            'nand_down': 'v',
            'nand_left': '<',
            'nand_right': '>',
        }

        # 4-b)it indexed. Bits are true if there is a neighbour:
        # Bottom Top Right Left
        self.wire_glyphs = [
            'o', '╸', '╺', '━',
            '╹', '┛', '┗', '┻',
            '╻', '┓', '┏', '┳',
            '┃', '┫', '┣', '╋'
        ]

        logger.info("----------------------------------")
        logger.info("Terminal colors: %d", self.t.number_of_colors)
        logger.info("Terminal size: %dx%d", self.t.width, self.t.height)

    def editor_loop(self):
        while True:
            self.render()

            # Get input
            inp = self.t.inkey()
            logger.debug('Key Input: ' + repr(inp))

            action = self.handle_inputs(inp)

            move = action.get('move')
            tile_toggle = action.get('tile_toggle')
            tile_set = action.get('tile_set')

            if action.get('exit'):
                break
            elif action.get('debug'):
                # Print out a bunch of debug stuff
                logger.debug('This is the debug string.')
                # Iterate through the entire grid, print out all the labels.
                for wire in self.grid.get_all_wire():
                    logger.debug(wire)

            elif move:
                new_cursor_pos = (
                    self.cursor_pos[0] + move[0],
                    self.cursor_pos[1] + move[1],
                )
                # Make sure the cursor coords don't end up negative
                if min(new_cursor_pos) >= 0:
                    self.cursor_pos = new_cursor_pos
                logger.debug('Cursor pos: %s', self.cursor_pos)
            elif tile_toggle:
                # Toggle between tile pieces
                x, y = self.cursor_pos
                try:
                    current = self.grid.tiles[y][x]
                except IndexError:
                    logger.debug('Cannot toggle out of bounds. Ignoring.')
                    continue
                new = None if current else Wire()
                self.grid.change_tile((x, y), new)
                # Tile((current.value + tile_toggle['direction']) % len(Tile))
            elif tile_set:
                x, y = self.cursor_pos
                current = self.grid.tiles[y][x]
                if isinstance(current, Nand):
                    current.rotate_facing(1)
                else:
                    self.grid.change_tile((x, y), Nand())



    def render(self):
        def neighbour_glyph_index(x, y):
            neighbours_tiles = map(lambda t: self.grid.get(*t), self.grid.get_neighbours_coords((x,y)))
            nearby_tiles = [isinstance(t,Wire) or isinstance(t, Nand) for t in neighbours_tiles]
            return (1 * nearby_tiles[0] +
                    2 * nearby_tiles[1] +
                    4 * nearby_tiles[2] +
                    8 * nearby_tiles[3])

        print(self.t.clear())

        components = self.grid.find_components()
        logger.info(components)

        # Render the grid
        print(self.t.move(0, 0), end='')
        for y in range(len(self.grid.tiles)):
            for x in range(len(self.grid.tiles[y])):
                # Get the glyph which represents this tile
                # glyph = self.glyphs.get(self.grid.tiles[y][x], '?')
                glyph = self.t.bright_black('.')
                tile = self.grid.tiles[y][x]
                if isinstance(tile, Wire):
                    color = components['tile_lookup'][(x,y)] + 1
                    if self.args.box_draw:
                        glyph = self.wire_glyphs[neighbour_glyph_index(x, y)]
                        glyph = self.t.color(color)(glyph)
                    else:
                        glyph = self.t.color(color)('+')
                elif isinstance(tile, Nand):
                    facings = ['^', '>', 'v', '<']
                    glyph = self.t.bold_black_on_white(facings[tile.facing])

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
