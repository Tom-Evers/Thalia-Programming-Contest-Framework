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
        self.enemy_ship_type_count = {Ship.CARRIER: 1,
                                      Ship.BATTLESHIP: 2,
                                      Ship.CRUISER: 3,
                                      Ship.DESTROYER: 4}
        self.own_ship_type_count = {Ship.CARRIER: 1,
                                    Ship.BATTLESHIP: 2,
                                    Ship.CRUISER: 3,
                                    Ship.DESTROYER: 4}
        self.enemy_multiplier_map = make_field_with_value(1)
        self.enemy_possible_ships = self.init_possible_ships(self.enemy_ship_type_count)
        self.own_possible_ships = self.init_possible_ships(self.own_ship_type_count)
        self.own_multiplier_map = make_field_with_value(1)
        self.already_picked = []

    def init_possible_ships(self, ships):
        poss = []
        for ship_size, ship_count in ships.items():
            for n in range(ship_count):
                for x in range(DIMENSIONS[X]):
                    for y in range(DIMENSIONS[Y] - ship_size + 1):
                        coords = []
                        for i in range(ship_size):
                            coords.append((x, y + i))
                        poss.append((n, coords))
                for y in range(DIMENSIONS[Y]):
                    for x in range(DIMENSIONS[X] - ship_size + 1):
                        coords = []
                        for i in range(ship_size):
                            coords.append((x + i, y))
                        poss.append((n, coords))
        return poss

    def get_shipcounts(self):
        return Counter([y for _, x in self.enemy_possible_ships for y in x])
        # result = []
        # for id, y in self.enemy_possible_ships:
        #     for _ in range(self.enemy_ship_type_count[t]):
        #         result += y
        # return Counter(result)

    def get_top_of_heatmap(self):
        max_val = 0
        max_coords = []
        counts = self.get_shipcounts()
        for x in range(DIMENSIONS[X]):
            for y in range(DIMENSIONS[Y]):
                xy_multiplier = self.enemy_multiplier_map[x][y]
                cur_val = counts[(x, y)] * xy_multiplier
                if cur_val > max_val:
                    max_val = cur_val
                    max_coords = [(x, y)]
                elif cur_val == max_val:
                    max_coords.append((x, y))
        return random.choice(max_coords)

    def get_bottom_of_heat_map(self, heatmap):

        # result = []
        # for t, y in heatmap:
        #     for _ in range(self.enemy_ship_type_count[t]):
        #         result += y
        # counts = Counter(result)
        # # if len(counts) >= 5:
        # #     least_likely = counts.most_common()[-5:]
        # # else:
        # #     least_likely = counts.most_common()
        # # likely_ = random.choice(least_likely)[0]
        counts = Counter([y for _, x in self.enemy_possible_ships for y in x])
        likely_ = counts.most_common()[-1][0]
        # print(str(likely_))
        return likely_

    def remove_ship_from_heatmap(self, sunk):
        # self.possible_ships = list(filter(lambda pos: sunk is not pos[0], self.possible_ships))
        # self.enemy_ship_type_count[sunk] -= 1  # FIXME: Kan dit onder de 0?
        return list(filter(lambda x: x[0] != self.enemy_ship_type_count[sunk] or len(x[1]) != sunk,
                           self.enemy_possible_ships))

    def remove_location_from_heatmap(self, x, y):
        self.enemy_possible_ships = list(filter(lambda pos: (x, y) not in pos[1], self.enemy_possible_ships))

    def increase_likelihood_around(self, x, y, prev=HOR):
        if x - 1 >= 0: self.enemy_multiplier_map[x - 1][y] *= 1000
        if x + 1 < DIMENSIONS[X]: self.enemy_multiplier_map[x + 1][y] *= 1000
        if y - 1 >= 0: self.enemy_multiplier_map[x][y - 1] *= 1000
        if y + 1 < DIMENSIONS[Y]: self.enemy_multiplier_map[x][y + 1] *= 1000

    def choose_ship_location(self):
        ship_type = self.choose_ship_size()
        possible_ship_locations = list(filter(lambda pos: ship_type == len(pos[1]), self.own_possible_ships))
        possible_ship_locations = list(map(lambda x: (self.accumulated_heat(x), x), possible_ship_locations))
        possible_ship_locations.sort()
        # pref = []
        # first = possible_ship_locations[0][0]
        # for pos in possible_ship_locations:
        #     if first != pos[0]:
        #         break
        #     pref.append(pos)
        loc = possible_ship_locations[1][1][1]
        print(str(loc))
        for coords in loc:
            self.own_possible_ships = list(filter(lambda pos: coords not in pos[1], self.own_possible_ships))
        for (x, y) in loc:
            for (nx, ny) in [(x - 1, y), (x, y - 1), (x + 1, y), (x, y + 1)]:
                if (nx, ny) not in loc:
                    if nx >= 0 and nx < DIMENSIONS[X] and ny >= 0 and ny < DIMENSIONS[Y]:
                        self.own_multiplier_map[nx][ny] *= 10
        return loc[0], loc[-1]

    # def choose_ship_location(self):
    #     ship_type = self.choose_ship_size()
    #     possible_locations = list(filter(lambda pos: ship_type == pos[0], self.own_possible_ships))
    #     loc = random.choice(possible_locations)[1]
    #     # unlikely = self.get_bottom_of_heat_map(possible_locations)
    #     # loc = random.choice(list(filter(lambda pos: unlikely in pos[1], possible_locations)))[1]
    #     for coord in loc:
    #         self.own_possible_ships = list(filter(lambda pos: coord not in pos[1], self.own_possible_ships))
    #     return loc[0], loc[-1]

    def choose_island_location(self):
        coords = self.get_top_of_heatmap()

        self.remove_location_from_heatmap(*coords)
        return coords

    def choose_shot_location(self):
        shot_loc = self.get_top_of_heatmap()
        if shot_loc in self.already_picked:
            print("Already picked {}".format(str(shot_loc)))
            all_coords = []
            for x in range(DIMENSIONS[X]):
                for y in range(DIMENSIONS[Y]):
                    all_coords.append((x, y))
            pickone = list(filter(lambda x: x not in self.already_picked, all_coords))
            already = random.choice(pickone)
            self.already_picked.append(already)
            return already
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
                    print(str(t))
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
                self.enemy_multiplier_map[x][y] = 0
                self.increase_likelihood_around(x, y, self.to_prev(x, y))  # HIERRRR
                print('---------------------------------')
                print('Result was SUNK')
                print('---------------------------------')
            else:
                self.increase_likelihood_around(x, y, self.to_prev(x, y))
                self.enemy_multiplier_map[x][y] = 0
                print('---------------------------------')
                print('Result was HIT')
                print('---------------------------------')
        else:
            self.remove_location_from_heatmap(x, y)
            self.enemy_multiplier_map[x][y] = 0
            print('---------------------------------')
            print('Result was MISS')
            print('---------------------------------')
        print('')
        print('Multiplier map:')
        print('\n'.join(list(map(str, self.enemy_multiplier_map))))
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
                start[x][y] = counts[(x, y)] * self.enemy_multiplier_map[x][y]
        return start

    def to_prev(self, _, y):
        return self.already_picked[-1][1] != y

    def accumulated_heat(self, ship_type_and_loc):
        ship_type, ship_coords = ship_type_and_loc

        def get_counts():
            return Counter([y for _, x in self.own_possible_ships for y in x])
            # result = []
            # for t, y in self.own_possible_ships:
            #     for _ in range(self.own_ship_type_count[t]):
            #         result += y
            # return Counter(result)

        counts = get_counts()
        acc_heat = 0
        for coord in ship_coords:
            acc_heat += counts[coord] * self.own_multiplier_map[coord[0]][coord[1]]  # HIERRR
            # acc_heat += (100 - counts[coord]) * self.own_multiplier_map[coord[0]][coord[1]]
        return acc_heat


if __name__ == "__main__":
    Asterix().run()
