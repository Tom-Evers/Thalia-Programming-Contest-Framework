#!/usr/bin/python3
from collections import Counter

from Bot import *
from api import *

# UNTOUCHED = 0
# MISS = 1
# HIT = 2
# SUNK = 3

print = lambda x: sys.stderr.write(x + '\n')
HOR = True
VER = False


class Asterix(Bot):
    def __init__(self):
        super().__init__()
        # self.activity_map = make_field_with_value(UNTOUCHED)
        self.ship_type_count = {Ship.CARRIER: 1,
                                Ship.BATTLESHIP: 2,
                                Ship.CRUISER: 3,
                                Ship.DESTROYER: 4}
        self.multiplier_map = make_field_with_value(1)
        self.enemy_possible_ships = self.init_possible_ships()
        self.own_possible_ships = self.init_possible_ships()
        self.already_picked = []

    def init_possible_ships(self):
        result = []
        for ship_type, _ in self.ship_type_count.items():
            for dir in [HORIZONTAL, VERTICAL]:
                for x in range(DIMENSIONS[X] - ship_type * dir[X]):
                    for y in range(DIMENSIONS[Y] - ship_type * dir[Y]):
                        result.append((ship_type, list_coords(x, y, dir, ship_type)))
        return result

    def get_shipcounts(self):
        # return Counter([stuff for stuff in [[x] * self.ship_type_count[t] for t, y in self.possible_ships for x in y]])
        result = []
        for t, y in self.enemy_possible_ships:
            for _ in range(self.ship_type_count[t]):
                result += y
        print('')
        print('Shipcounts: {}'.format(str(Counter(result))))
        return Counter(result)

    def get_top_of_heatmap(self):
        max_val = 0
        max_coords = []
        counts = self.get_shipcounts()
        for x in range(DIMENSIONS[X]):
            for y in range(DIMENSIONS[Y]):
                xy_multiplier = self.multiplier_map[x][y]
                cur_val = counts[(x, y)] * xy_multiplier
                if cur_val > max_val:
                    max_val = cur_val
                    max_coords = [(x, y)]
                elif cur_val == max_val:
                    max_coords.append((x, y))
        return random.choice(max_coords)

    def get_bottom_of_heat_map(self, heatmap):
        result = []
        for t, y in heatmap:
            for _ in range(self.ship_type_count[t]):
                result += y
        counts = Counter(result)
        # if len(counts) >= 5:
        #     least_likely = counts.most_common()[-5:]
        # else:
        #     least_likely = counts.most_common()
        # likely_ = random.choice(least_likely)[0]
        likely_ = counts.most_common()[-1][0]
        # print(str(likely_))
        return likely_

    def remove_ship_from_heatmap(self, sunk):
        # self.possible_ships = list(filter(lambda pos: sunk is not pos[0], self.possible_ships))
        self.ship_type_count[sunk] -= 1  # FIXME: Kan dit onder de 0?

    def remove_location_from_heatmap(self, x, y):
        self.enemy_possible_ships = list(filter(lambda pos: (x, y) not in pos[1], self.enemy_possible_ships))

    def increase_likelihood_around(self, x, y, prev=HOR):
        if x - 1 >= 0: self.multiplier_map[x - 1][y] *= 10 if prev else 5
        if x + 1 < DIMENSIONS[X]: self.multiplier_map[x + 1][y] *= 10 if prev else 5
        if y - 1 >= 0: self.multiplier_map[x][y - 1] *= 10 if not prev else 5
        if y + 1 < DIMENSIONS[Y]: self.multiplier_map[x][y + 1] *= 10 if not prev else 5

    def choose_ship_location(self):
        ship_type = self.choose_ship_size()
        possible_locations = list(filter(lambda pos: ship_type == pos[0], self.own_possible_ships))
        loc = random.choice(possible_locations)[1]
        # unlikely = self.get_bottom_of_heat_map(possible_locations)
        # loc = random.choice(list(filter(lambda pos: unlikely in pos[1], possible_locations)))[1]
        for coord in loc:
            self.own_possible_ships = list(filter(lambda pos: coord not in pos[1], self.own_possible_ships))
        return loc[0], loc[-1]

    def choose_island_location(self):
        coords = self.get_top_of_heatmap()

        self.remove_location_from_heatmap(*coords)
        return coords

    def choose_shot_location(self):
        shot_loc = self.get_top_of_heatmap()
        if shot_loc in self.already_picked:
            print("Already picked {}".format(str(shot_loc)))
        else:
            self.already_picked.append(shot_loc)
        return shot_loc

    def choose_ship_size(self):
        return super().choose_ship_size()
        # You may want to extend this method, but it is not required.

    def handle_result(self, text):
        super().handle_result(text)

        def parse(t):
            if "HIT" in t:
                if "YOUSUNKMY" in t:
                    return True, Ship[t.split()[-1]]
                else:
                    return True, None
            else:
                return False, None

        hit, sunk = parse(text)
        x, y = self.lastCoord
        if hit:
            if sunk is not None:
                self.remove_location_from_heatmap(x, y)
                self.remove_ship_from_heatmap(sunk)
                self.multiplier_map[x][y] = 0
                print('---------------------------------')
                print('Result was SUNK')
                print('---------------------------------')
            else:
                self.increase_likelihood_around(x, y, self.to_prev(x, y))
                self.multiplier_map[x][y] = 0
                print('---------------------------------')
                print('Result was HIT')
                print('---------------------------------')
        else:
            self.remove_location_from_heatmap(x, y)
            self.multiplier_map[x][y] = 0
            print('---------------------------------')
            print('Result was MISS')
            print('---------------------------------')
        print('')
        print('Multiplier map:')
        print('\n'.join(list(map(str, self.multiplier_map))))
        print('')
        print('Heatmap')
        print('\n'.join(list(map(str, self.to_heatmap()))))

    def handle_update(self, text):
        super().handle_update(text)
        if text.find("RESULT GOTISLAND"):
            tokens = text.strip().split()
            coord = (int(re.sub("\D", "", tokens[2])),
                     int(re.sub("\D", "", tokens[3])))
            self.own_possible_ships = list(filter(lambda pos: coord not in pos[1], self.own_possible_ships))

        # You may want to extend this method, but it is not required.

    def to_heatmap(self):
        start = make_field_with_value(0)
        counts = self.get_shipcounts()
        for x in range(DIMENSIONS[X]):
            for y in range(DIMENSIONS[Y]):
                start[x][y] = counts[(x, y)] * self.multiplier_map[x][y]
        return start

    def to_prev(self, _, y):
        return self.already_picked[-1][1] == y


if __name__ == "__main__":
    Asterix().run()
