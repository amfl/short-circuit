# Coord releated


def add(tup1, tup2):
    """
    TODO Replace me with something sensible
    """
    return (tup1[0] + tup2[0], tup1[1] + tup2[1])


def invert(tup):
    """Inverts a tuple."""
    a, b = tup
    return (-a, -b)

# Board releated


def neighbour_deltas():
    return [(0, -1), (1, 0), (0, 1), (-1, 0)]


def neighbour_coords(coords):
    return [add(coords, x) for x in neighbour_deltas()]
