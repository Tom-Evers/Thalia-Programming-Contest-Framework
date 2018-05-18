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


PLAYERS = [1, 2]
FIELDS = {}
for P in PLAYERS:
    FIELDS[P] = make_field_with_value(EMPTY), []


def place_island(x, y, player):
    if FIELDS[player][0][x][y] != EMPTY:
        raise ("How can you pick an island here?")
    else:
        FIELDS[player][0][x][y] = ISLAND


def list_coords(x, y, dir, length):
    result = []
    for i in range(length):
        result.append((x + i * dir[X], y + i * dir[Y]))
    return result
