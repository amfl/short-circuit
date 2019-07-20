import logging

from graph.proto import *
from tile.tui import *


logger = logging.getLogger()
logname = 'gameplay.log'
logging.basicConfig(filename=logname,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(module)s %(levelno)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

def main():
    # Run the prototype code for graph representation
    proto()

    # Start up the UI
    t = TermUI()
    # Block until we quit the UI
    t.start()

if __name__ == '__main__':
    main()
