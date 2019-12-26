import queue
import logging

from board import Board

logger = logging.getLogger()


class World:
    def __init__(self, boards):
        self.boards = boards
        self.queue = queue.Queue()

    def submit(self, arg):
        """Submits a message into the message queue."""
        self.queue.put(arg)

    def start(self):
        """Starts reading from the queue. Blocks until we receive the quit
        message."""
        while True:
            self.process_queue()

    def process_queue(self):
        """Reads a single message from the queue."""
        message = self.queue.get()
        logger.info(f"Got message: {message}")

        tile_set = message.get('tile_set')
        nand_rotate = message.get('nand_rotate')
        tick = message.get('tick')
        switch_toggle = message.get('switch_toggle')

        if tile_set:
            node = Board.deserialize_simnode(tile_set['node'])
            coord = tile_set['coord']
            index = tile_set['index']
            self.boards[index].set(coord, node)

        elif nand_rotate:
            coord = nand_rotate['coord']
            index = nand_rotate['index']
            delta = nand_rotate['delta']

            board = self.boards[index]
            nand = board.get(coord)

            nand.rotate_facing(delta, coord, board)

        elif switch_toggle:
            coord = switch_toggle['coord']
            index = switch_toggle['index']
            value = switch_toggle['value']

            board = self.boards[index]
            switch = board.get(coord)

            switch.toggle(value)

        elif tick:
            for board in self.boards:
                board.tick()
