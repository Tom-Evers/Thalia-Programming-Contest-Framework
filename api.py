X, Y = 'x', 'y'
DIMENSIONS = {X: 10, Y: 10}
BOATS = [5, 4, 3, 3, 2]
VERTICAL = {X: 0, Y: 1}
HORIZONTAL = {X: 1, Y: 0}
EMPTY = 0
SHIP = 1
ISLAND = 2
N_ISLANDS = 5


def make_field_with_value(value):
    return [[value for _ in range(DIMENSIONS[Y])] for _ in range(DIMENSIONS[X])]
