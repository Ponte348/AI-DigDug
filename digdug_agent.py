# Joao Oliveira 110532
# Pedro Ponte 98059
# Filipe Posio 80709
import copy
from enum import Enum
import math
from comandos import Comandos

from consts import Tiles, Direction
import math

from search import AURA_FRONT_COST, AURA_SIDE_COST, BOULDER_COST, ENEMY_COST, FYGAR_FIRE_COST, SearchDomain, SearchProblem, SearchTree, SearchNode, PASSAGE_COST, ROCK_COST

class Estado(Enum):
    IDLE = 1
    CHASE = 2


class DigDugAgent:
    def __init__(self):
        self.estado_atual = Estado.IDLE
        self.position = None
        self.key = Comandos.MOVE_LEFT
        self.direction = Direction.WEST

        self.current_target = {'enemy': None, 'distance': float('inf')}
        self.max_depth_search = 5
        self.min_depth_search = 1
        self.radar_distance = 5
        self.map_topology = []


    def act(self, game_state):
        self.key = Comandos.IDLE
        if "step" not in game_state:
            if "map" in game_state:
                self.map_topology = copy.deepcopy(game_state["map"])
                self.domain = SearchDomain(game_state["size"])

        if "enemies" not in game_state or game_state["enemies"] == []:
            return self.key


        if self.estado_atual == Estado.IDLE:
            self.position = game_state["digdug"]
            
            enemy_by_distance = [(enemy, distance(self.position, enemy["pos"])) for enemy in game_state["enemies"]]
            enemy_by_distance.sort(key = lambda enemy: enemy[1])

            self.current_target = enemy_by_distance[0][0]
            self.estado_atual = Estado.CHASE

            return self.key

        elif self.estado_atual == Estado.CHASE:
            if self.current_target is None:
                self.estado_atual = Estado.IDLE
                return self.key
            
            if not any(enemy["id"] == self.current_target["id"] for enemy in game_state["enemies"]):
                self.current_target = None
                self.estado_atual = Estado.IDLE
                return self.key
            
            self.position = game_state["digdug"]
            self.current_target = [enemy for enemy in game_state["enemies"] if (enemy["id"] == self.current_target["id"]) ][0]

            map_costs = [[PASSAGE_COST if cell == 0 else ROCK_COST for cell in col] for col in self.map_topology]
            
            for boulder in game_state['rocks']:
                x, y = boulder['pos']
                map_costs[x][y] += BOULDER_COST
                # if (0 <= y + 1 < self.domain.map_dimensions[1]) and self.map_topology[x][y+1] in [Tiles.PASSAGE.value, Tiles.STONE.value]:
                #     map_costs[x][y+1] += BOULDER_COST
            
            for e in game_state['enemies']:
                x, y = e['pos']
                direction = e['dir']
                map_costs[x][y] += ENEMY_COST
                if direction == Direction.NORTH.value:
                    self.add_enemy_aura_specific(map_costs, [
                                                    (x, y-3, AURA_FRONT_COST),
                                                    (x, y-2, AURA_FRONT_COST),
                        (x-1, y-1, AURA_SIDE_COST), (x, y-1, AURA_FRONT_COST),  (x+1, y-1, AURA_SIDE_COST),
                        (x-1, y, AURA_SIDE_COST),                               (x+1, y, AURA_SIDE_COST),
                        (x-1, y+1, AURA_SIDE_COST),                             (x+1, y+1, AURA_SIDE_COST)
                    ])
                elif direction == Direction.EAST.value:
                    self.add_enemy_aura_specific(map_costs, [
                        (x-1, y-1, AURA_SIDE_COST), (x, y-1, AURA_SIDE_COST),   (x+1, y-1, AURA_SIDE_COST),
                                                                                (x+1, y, AURA_FRONT_COST),  (x+2, y, AURA_FRONT_COST), (x+3, y, AURA_FRONT_COST),
                        (x-1, y+1, AURA_SIDE_COST), (x, y+1, AURA_SIDE_COST),   (x+1, y+1, AURA_SIDE_COST)
                    ])
                elif direction == Direction.SOUTH.value:
                    self.add_enemy_aura_specific(map_costs, [
                        (x-1, y-1, AURA_SIDE_COST),                             (x+1, y-1, AURA_SIDE_COST),
                        (x-1, y, AURA_SIDE_COST),                               (x+1, y, AURA_SIDE_COST),
                        (x-1, y+1, AURA_SIDE_COST), (x, y+1, AURA_FRONT_COST),  (x+1, y+1, AURA_SIDE_COST),
                                                    (x, y+2, AURA_FRONT_COST),
                                                    (x, y+3, AURA_FRONT_COST)
                    ])
                elif direction == Direction.WEST.value:
                    self.add_enemy_aura_specific(map_costs, [
                                                                                (x-1, y-1, AURA_SIDE_COST), (x, y-1, AURA_SIDE_COST),   (x+1, y-1, AURA_SIDE_COST),
                        (x-3, y, AURA_FRONT_COST),  (x-2, y, AURA_FRONT_COST),  (x-1, y, AURA_FRONT_COST),
                                                                                (x-1, y+1, AURA_SIDE_COST), (x, y+1, AURA_SIDE_COST),   (x+1, y+1, AURA_SIDE_COST),
                    ])
                if e['name'] == 'Fygar' and 'fire' in e:
                    for fire in e['fire']:
                        fire_x, fire_y = fire
                        map_costs[fire_x][fire_y] += FYGAR_FIRE_COST
            
            initial_state = {
                "position": self.position,
                "score": 0,
                "enemies": game_state["enemies"],
                "boulders": game_state["rocks"],
                "map_topology": self.map_topology,
                "map": map_costs,
                "target": self.current_target,
                "key": self.key,
                "direction": self.direction
            }

            goal_state = {
                "position": self.current_target["pos"],
                "score": 0,
                "enemies": []
            }

            depth_search = self.max_depth_search\
                                if any([math.dist(initial_state["position"], e["pos"]) <= self.radar_distance
                                        for e in game_state["enemies"]])\
                                else self.min_depth_search
            
            problem = SearchProblem(self.domain, initial_state, goal_state)
            tree = SearchTree(problem, "a*", depth_search)
            search_result = tree.search()
            
            if search_result:
                if len(search_result) == 1 or search_result[0] == search_result[1]:
                    self.key = Comandos.SHOOT
                else:
                    self.key = self.get_move_command_to_target(self.position, search_result[1])
            else:
                self.key = Comandos.SHOOT
            update_map(self.map_topology, self.position, self.key)
            return self.key
        
    def get_move_command_to_target(self, start, target):
        start_x, start_y = start
        target_x, target_y = target

        if target_y < start_y:
            self.direction = Direction.NORTH
            return Comandos.MOVE_UP
        elif target_y > start_y:
            self.direction = Direction.SOUTH
            return Comandos.MOVE_DOWN
        elif target_x < start_x:
            self.direction = Direction.WEST
            return Comandos.MOVE_LEFT
        elif target_x > start_x:
            self.direction = Direction.EAST
            return Comandos.MOVE_RIGHT

        return Comandos.IDLE

    def add_enemy_aura(self, mapa, min_width, max_width, min_height, max_height, safe_position):
        safe_x, safe_y = safe_position

        for x in range(min_width, max_width+1):
            for y in range(min_height, max_height+1):
                if (0 <= x < self.domain.map_dimensions[0]) and (0 <= y < self.domain.map_dimensions[1]):
                    mapa[x][y] += AURA_FRONT_COST
    
        if(0 <= safe_x < self.domain.map_dimensions[0]) and (0 <= safe_y < self.domain.map_dimensions[1]):
            mapa[safe_x][safe_y] -= AURA_FRONT_COST

    def add_enemy_aura_specific(self, mapa, aura_positions):
        for x, y, cost in aura_positions:
            if (0 <= x < self.domain.map_dimensions[0]) and (0 <= y < self.domain.map_dimensions[1]):
                mapa[x][y] += cost
        

def update_map(mapa, position, key):
    if key in [Comandos.IDLE, Comandos.SHOOT]:
        return

    x, y = position

    if key == Comandos.MOVE_UP:
        y -= 1
    elif key == Comandos.MOVE_DOWN:
        y += 1
    elif key == Comandos.MOVE_LEFT:
        x -= 1
    elif key == Comandos.MOVE_RIGHT:
        x += 1

    mapa[x][y] = 0

def distance(start, target):
    return math.floor(math.dist(start, target))

def in_radar(start, target, radar_distance):
    x, y = start
    tx, ty = target
    return (abs(x-tx) <= radar_distance) and (abs(y-ty) <= radar_distance)