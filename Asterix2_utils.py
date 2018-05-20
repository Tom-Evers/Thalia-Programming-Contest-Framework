from collections import Counter

from Bot import *

X = 0
Y = 1
SHIP_TYPE = 0
COORDS = 1
CAUSED_BY = 0
LEFT = True
RIGHT = False


def parse(t):
    if "HIT" in t:
        return True, (Ship[t.split()[-1]] if "YOUSUNKMY" in t else None)
    else:
        return False, None


def make_field_with_value(value, dims):
    return [[value for _ in range(dims[Y])] for _ in range(dims[X])]


def highest_heat(possible_ships):
    return Counter([y for _, x in possible_ships for y in x])


def remove_location_from_possible_ships(coords, possible_ships):
    return list(filter(lambda ship_coord_combo: coords not in ship_coord_combo[1], possible_ships))


def remove_ship_from_possible_ships(ship, possible_ships, ships_left):
    return list(filter(lambda x: x[0] != ships_left[ship] or len(x[1]) != ship, possible_ships))


def within_bounds(coords, dims):
    return 0 <= coords[X] < dims[X] and 0 <= coords[Y] < dims[Y]


def append_prio_switch(queue, data, prio):
    """prio=True inserts to the left."""
    queue.appendleft(data) if prio else queue.append(data)


def init_possible_ships(ships, dims):
    poss = []
    for ship_size, ship_count in ships.items():
        for n in range(ship_count):
            for x in range(dims[X]):
                for y in range(dims[Y] - ship_size + 1):
                    coords = []
                    for i in range(ship_size):
                        coords.append((x, y + i))
                    poss.append((n, coords))
            for y in range(dims[Y]):
                for x in range(dims[X] - ship_size + 1):
                    coords = []
                    for i in range(ship_size):
                        coords.append((x + i, y))
                    poss.append((n, coords))
    return poss


def to_heatmap(possible_ships, dims):
    heatmap = make_field_with_value(0, dims)
    for id, coord_list in possible_ships:
        for (x, y) in coord_list:
            heatmap[x][y] += 1
    return '\n'.join(list(map(lambda y: str(list(map(lambda x: str(x).rjust(3), y))), heatmap)))


def coords_left(history, dims):
    all = []
    for x in range(dims[X]):
        for y in range(dims[Y]):
            all.append((x, y))
    return list(filter(lambda coord: coord not in history, all))
