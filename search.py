# Joao Oliveira 110532
# Pedro Ponte 98059
# Filipe Posio 80709

from comandos import Comandos
from celulas import Celulas
from enum import Enum

from consts import Tiles, Direction
import math

PASSAGE_COST = 1
ROCK_COST = 1.5
ENEMY_COST = 300
AURA_FRONT_COST = 100
AURA_SIDE_COST = 30
BOULDER_COST = 300
FYGAR_FIRE_COST = 300


class SearchDomain():
    def __init__(self, map_dimensions) -> None:
        self.map_dimensions = map_dimensions
        self.shoot_range = 3

    def actions(self, state):
        x, y = state["position"]
        actions = []

        if self.shootable_target(state["position"], state["enemies"], state["direction"], state["boulders"], state["map_topology"]):
            actions.append(Comandos.SHOOT)

        moves = {
            Comandos.MOVE_UP: [x, y-1],
            Comandos.MOVE_DOWN: [x, y+1],
            Comandos.MOVE_LEFT: [x-1, y],
            Comandos.MOVE_RIGHT: [x+1, y]
        }

        actions += [comando for comando, position in moves.items()\
                        if self.is_inside_map(position)\
                        and not any(boulder["pos"] == position for boulder in state["boulders"])]

        return actions

    def result(self, state, action):
        result = {
            "position": state["position"],
            "score": state["score"],
            "enemies": state["enemies"],
            "boulders": state["boulders"],
            "map_topology": state["map_topology"],
            "map": state["map"],
            "target": state["target"],
            "key": state["key"],
            "direction": state["direction"]
        }

        x, y = state["position"]
        move_actions = {
            Comandos.MOVE_UP: ([x, y-1], Direction.NORTH),
            Comandos.MOVE_DOWN: ([x, y+1], Direction.SOUTH),
            Comandos.MOVE_LEFT: ([x-1, y], Direction.WEST),
            Comandos.MOVE_RIGHT: ([x+1, y], Direction.EAST)
        }

        if action in move_actions:
            new_pos, new_dir = move_actions[action]
            result["position"] = new_pos
            result["direction"] = new_dir
            result["key"] = action
            result["score"] = 0
            return result
        
        elif action == Comandos.SHOOT:
            result["key"] = Comandos.SHOOT
            result["score"] = 2
            return result

    def satisfies(self, state, goal):
        return self.shootable_target(state["position"], state["enemies"], state["direction"], state["boulders"], state["map_topology"])

    def cost(self, state, action):
        x, y = state["position"]

        if action == Comandos.MOVE_DOWN:
            y += 1
            return state["map"][x][y]
        elif action == Comandos.MOVE_UP:
            y -= 1
            return state["map"][x][y]
        elif action == Comandos.MOVE_LEFT:
            x -= 1
            return state["map"][x][y]
        elif action == Comandos.MOVE_RIGHT:
            x += 1
            return state["map"][x][y]
        elif action == Comandos.SHOOT:
            return 0

    def heuristic(self, state, goal):
        x, y = state["position"]
        target_x, target_y = goal["position"]

        return math.dist(state["position"], goal["position"])

    def is_inside_map(self, position):
        x, y = position
        w, h = self.map_dimensions

        return (0 <= x < w) and (0 <= y < h)

    def shootable_target(self, position, enemies, direction, boulders, map_topology):
        enemies_in_range = [enemy for enemy in enemies\
                            if self.aligned(position, enemy["pos"])
                            and self.in_range(position, enemy["pos"])]
        if not enemies_in_range:
            return False
        
        if any(self.open_shot(position, enemy["pos"], direction, map_topology) for enemy in enemies_in_range):
            return True
    
    def aligned(self, position, target):
        px, py = position
        tx, ty = target
        return px==tx or py==ty
    
    def inside_map(self, position):
        x, y = position
        width, height = self.map_dimensions
        return (0 <= x < width) and (0 <= y < height)
    
    def in_range(self, position, target):
        px, py = position
        tx, ty = target

        return (abs(px-tx) + abs(py-ty)) <= self.shoot_range
    
    def open_shot(self, position, target, direction, map_topology):
        x, y = position
        if direction == Direction.NORTH:
            offset = 1
            while offset <= self.shoot_range:
                aim = [x, y-offset]
                if not self.inside_map(aim):
                    return False
                if map_topology[aim[0]][aim[1]] == Tiles.STONE.value:
                    return False
                if aim == target:
                    return True
                offset += 1
            return False
        if direction == Direction.SOUTH:
            offset = 1
            while offset <= self.shoot_range:
                aim = [x, y+offset]
                if not self.inside_map(aim):
                    return False
                if map_topology[aim[0]][aim[1]] == Tiles.STONE.value:
                    return False
                if aim == target:
                    return True
                offset += 1
            return False
        if direction == Direction.EAST:
            offset = 1
            while offset <= self.shoot_range:
                aim = [x+offset, y]
                if not self.inside_map(aim):
                    return False
                if map_topology[aim[0]][aim[1]] == Tiles.STONE.value:
                    return False
                if aim == target:
                    return True
                offset += 1
            return False
        if direction == Direction.WEST:
            offset = 1
            while offset <= self.shoot_range:
                aim = [x-offset, y]
                if not self.inside_map(aim):
                    return False
                if map_topology[aim[0]][aim[1]] == Tiles.STONE.value:
                    return False
                if aim == target:
                    return True
                offset += 1
            return False

class SearchProblem():
    def __init__(self, domain, initial, goal) -> None:
        self.domain = domain
        self.initial = initial
        self.goal = goal

    def goal_test(self, state):
        return self.domain.satisfies(state, self.goal)
    
class SearchNode():
    def __init__(self, state, parent, depth, cost, heuristic) -> None:
        self.state = state
        self.parent = parent
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
        self.value = cost + heuristic
        
    def __str__(self):
        state_without_map = {key: value for key, value in self.state.items() if key != 'map'}
        return f"SearchNode(state={state_without_map}, parent={self.parent}, depth={self.depth}, cost={self.cost})"

class SearchTree():
    def __init__(self, problem, strategy='dijkstra', max_depth=3) -> None:
        self.problem = problem
        root = SearchNode(problem.initial, None, 0, 0, 0)
        self.open_nodes = [root]
        self.strategy = strategy
        self.solution = None
        self.max_depth = max_depth
        self.best_solution = None
        self.visited_cells = []
        self.max_visited_cells = 3

    def get_path(self, node):
        if node.parent == None:
            return [node.state["position"]]
        path = self.get_path(node.parent)
        path += [node.state["position"]]
        return(path)
    
    def search(self):
        while self.open_nodes != []:
            node = self.open_nodes.pop(0)

            #todo repensar como se guarda as ultimas posições
            # de forma a que não crie ciclo, mas que permite
            # o dd voltar a posições anteriores
            
            if node.state["position"] in self.visited_cells:
                continue
            self.visited_cells.append(node.state["position"])
            if len(self.visited_cells) > self.max_visited_cells:
                self.visited_cells.pop(0)

            if self.problem.goal_test(node.state):
                self.solution = node
                return self.get_path(node)
            
            lnewnodes = []
            for action in self.problem.domain.actions(node.state):
                new_state = self.problem.domain.result(node.state, action)

                if new_state not in self.get_path(node) and (node.depth+1 <= self.max_depth):
                    action_cost = self.problem.domain.cost(node.state, action)
                    heuristic_cost = self.problem.domain.heuristic(new_state, self.problem.goal)
                    newnode = SearchNode(new_state, node, node.depth + 1, node.cost + action_cost, heuristic_cost)
                    lnewnodes.append(newnode)
            self.add_to_open(lnewnodes)

            if node.depth > 0 :
                if not self.best_solution\
                    or node.state["score"] > self.best_solution.state["score"]\
                    or (node.state["score"] == self.best_solution.state["score"] and node.value < self.best_solution.value):
                    self.best_solution = node
        
        if self.best_solution:
            return self.get_path(self.best_solution)
        else: 
            return None

    def add_to_open(self, lnewnodes):

        if self.strategy == "breadth":
            self.open_nodes.extend(lnewnodes)
        elif self.strategy == "depth":
            self.open_nodes[:0] = lnewnodes
        elif self.strategy == "a*":
            self.open_nodes.extend(lnewnodes)
            self.open_nodes.sort(key=lambda x: (x.state["score"], -(x.value)), reverse=True)