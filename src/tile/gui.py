import logging
from blessed import Terminal
from blessed.formatters import FormattingString

logger = logging.getLogger()

class TermGUI:
    def __init__(self):
        t = Terminal()

        logger.info("----------------------------------")
        logger.info("Terminal colors: %d", t.number_of_colors)
        logger.info("Terminal size: %dx%d", t.width, t.height)
