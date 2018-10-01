#!/usr/bin/python3
import operator
from collections import deque
from typing import Callable, Tuple

from Asterix2_utils import *


def print(x):
    sys.stderr.write(x + '\n')
    sys.stderr.flush()


class Asterix2(Bot):

    def __init__(self):
        super().__init__()
        self.relevant_history = []
        self.history = []
        self.search_direction = Dir.NORTH

        self.enemy_ships_left = {Ship.CARRIER: 1, Ship.BATTLESHIP: 2, Ship.CRUISER: 3, Ship.DESTROYER: 4}
        self.enemy_possible_ships = init_possible_ships(self.enemy_ships_left, self.enemyBoard.dims)
        self.priority = deque()  # (caused_by, coords)

        self.own_multipliers = make_field_with_value(1, self.ownBoard.dims)
        self.own_ships_left = {Ship.CARRIER: 1, Ship.BATTLESHIP: 2, Ship.CRUISER: 3, Ship.DESTROYER: 4}
        self.own_possible_ships = init_possible_ships(self.own_ships_left, self.ownBoard.dims)
        self.own_heatmap = make_field_with_value(0, self.ownBoard.dims)

    def remove_coord_from_priority(self, coord, key):
        new_queue = deque()
        while len(self.priority) > 0:
            item = self.priority.popleft()
            if item[key] != coord:
                new_queue.append(item)
        self.priority = new_queue

    def update_priorities_around_lastCoords(self):
        prev_x, prev_y = self.lastCoord
        left = prev_x - 1, prev_y
        right = prev_x + 1, prev_y
        top = prev_x, prev_y - 1
        bottom = prev_x, prev_y + 1

        priority = len(self.relevant_history) > 1
        priority_to_top_bottom = False
        priority_to_left_right = False
        if priority:
            priority_to_top_bottom = self.relevant_history[-2][0][X] == prev_x
            priority_to_left_right = not priority_to_top_bottom
        if within_bounds(top, self.enemyBoard.dims) and top not in self.history:
            append_prio_switch(self.priority, (self.lastCoord, top), priority and priority_to_top_bottom)
        if within_bounds(bottom, self.enemyBoard.dims) and bottom not in self.history:
            append_prio_switch(self.priority, (self.lastCoord, bottom), priority and priority_to_top_bottom)
        if within_bounds(left, self.enemyBoard.dims) and left not in self.history:
            append_prio_switch(self.priority, (self.lastCoord, left), priority and priority_to_left_right)
        if within_bounds(right, self.enemyBoard.dims) and right not in self.history:
            append_prio_switch(self.priority, (self.lastCoord, right), priority and priority_to_left_right)
        # FIXME: This doesn't work in the correct order.

    def update_relevant_history_and_priorities(self, hit, sunk):
        if hit:
            print('HIT!')
            self.relevant_history.append((self.lastCoord, hit, sunk))
            print(str(self.relevant_history))
            if sunk is not None:
                print('SUNK {}'.format(str(sunk)))
                coord = None
                for _ in range(sunk):
                    coord, _, _ = self.relevant_history.pop()
                    self.enemy_possible_ships = remove_location_from_possible_ships(coord, self.enemy_possible_ships)
                    self.remove_coord_from_priority(coord, CAUSED_BY)
                self.enemy_ships_left[sunk] -= 1
                self.enemy_possible_ships = remove_ship_from_possible_ships(sunk,
                                                                            self.enemy_possible_ships,
                                                                            self.enemy_ships_left)
            else:
                self.update_priorities_around_lastCoords()
                # TODO: Verder nog iets als je een hit hebt maar geen sunk?
        else:
            print('MISS!')
            self.enemy_possible_ships = remove_location_from_possible_ships(self.lastCoord, self.enemy_possible_ships)
        print("prios: {}".format(str(list(map(lambda x: x[1], self.priority)))))
        print("becos: {}".format(str(list(map(lambda x: x[0], self.priority)))))
        # print(to_heatmap(self.enemy_possible_ships, self.enemyBoard.dims))
        self.print_board(self.enemyBoard)

    def choose_ship_location(self):
        ship_type = self.choose_ship_size()
        _, all_coords = random.choice(list(filter(lambda x: len(x[1]) == ship_type, self.own_possible_ships)))
        for coord in all_coords:
            self.own_possible_ships = remove_location_from_possible_ships(coord, self.own_possible_ships)
        self.own_ships_left[ship_type] -= 1
        self.own_possible_ships = remove_ship_from_possible_ships(ship_type,
                                                                  self.own_possible_ships,
                                                                  self.own_ships_left)
        return all_coords[0], all_coords[-1]

    def choose_island_location(self):
        heats = highest_heat(self.enemy_possible_ships)
        coords, _ = heats.most_common()[0]
        self.enemy_possible_ships = remove_location_from_possible_ships(coords, self.enemy_possible_ships)
        return coords

    def choose_shot_location(self):
        if len(self.priority) > 0:
            _, coords = self.priority.popleft()
            self.remove_coord_from_priority(coords, COORDS)
        else:
            heats = highest_heat(self.enemy_possible_ships)
            try:
                coords, _ = heats.most_common()[0]
            except IndexError:
                coords = random.choice(coords_left(self.history, self.enemyBoard.dims))
                print("Had to pick a random coordinate. Is the game already over?")
        self.history.append(coords)
        return coords

    def choose_ship_size(self):
        # assert (all([cnt == self.own_ships_left[size] for size, cnt in self.shipsToPlace]))
        return super().choose_ship_size()
        # You may want to extend this method, but it is not required.

    def handle_result(self, text):
        super().handle_result(text)
        self.update_relevant_history_and_priorities(*parse(text))

    def handle_update(self, text):
        super().handle_update(text)
        if text.find("RESULT GOTISLAND"):
            tokens = text.strip().split()
            coord = (int(re.sub("\D", "", tokens[2])),
                     int(re.sub("\D", "", tokens[3])))
            self.own_possible_ships = remove_location_from_possible_ships(coord, self.own_possible_ships)
        # TODO: If island placement is according to highest probabilities, place ships least likely.

    def print_board(self, board):
        line = '\n' + '_____' * 10 + '___' * 9
        for x in range(board.dims[X]):
            line1 = ""
            line2 = ""
            for y in range(board.dims[Y]):
                try:
                    because, prio = list(map(list, zip(*list(filter(lambda p: (x, y) == p[1], self.priority)))))
                except ValueError:
                    because, prio = [], []
                if board.get((x, y)) == Tile.Ship:
                    line1 += '  X  '
                    line2 += '-----' if (x, y) in prio else '-{},{}-'.format(x, y)
                elif (x, y) in prio:
                    because = because[prio.index((x, y))]
                    line1 += '  {}  '.format(self.priority.index((because, (x, y))))
                    line2 += '({},{})'.format(*because)
                elif (x, y) in self.history:
                    line1 += '  M  '
                    line2 += '-----' if (x, y) in prio else '     '
                else:
                    line1 += '  ~  '
                    line2 += '-----' if (x, y) in prio else '     '
                line1 += ' | '
                line2 += ' | '
            print(line1)
            print(line2 + line)


if __name__ == "__main__":
    Asterix2().run()
