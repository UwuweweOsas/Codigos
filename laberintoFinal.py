import pygame
import pygame_gui
from collections import deque
import math 

pygame.init()

info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = info.current_w, info.current_h
NAVBAR_HEIGHT = 60

class Node:
    def __init__(self, state, parent, action):
        self.state = state
        self.parent = parent
        self.action = action

class StackFrontier:
    def __init__(self):
        self.frontier = []

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return not self.frontier

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        return self.frontier.pop()

class QueueFrontier:
    def __init__(self):
        self.frontier = deque()

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return not self.frontier

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        return self.frontier.popleft()

class GreedyFrontier:
    def __init__(self, goal):
        self.frontier = []
        self.goal = goal

    def add(self, node):
        priority = abs(node.state[0] - self.goal[0]) + abs(node.state[1] - self.goal[1])
        self.frontier.append((priority, node))
        self.frontier.sort(key=lambda x: x[0])

    def contains_state(self, state):
        return any(node.state == state for _, node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        return self.frontier.pop(0)[1]


class AStarFrontier:
    def __init__(self, start, goal):
        self.frontier = []
        self.goal = goal
        self.start = start
        self.g_costs = {start: 0}

    def add(self, node):
        g = self.g_costs[node.parent.state] + 1 if node.parent else 0
        h = abs(node.state[0] - self.goal[0]) + abs(node.state[1] - self.goal[1])
        f = g + h
        self.frontier.append((f, node))
        self.g_costs[node.state] = g
        self.frontier.sort(key=lambda x: x[0])

    def contains_state(self, state):
        return any(node.state == state for _, node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        return self.frontier.pop(0)[1]

class Maze:
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()

        if contents.count("A") != 1 or contents.count("B") != 1:
            raise Exception("El laberinto debe tener exactamente un punto de inicio y un punto de meta")

        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)
        self.walls = [[True if cell != ' ' and cell != 'A' and cell != 'B' else False for cell in line] for line in contents]
        self.start = [(i, j) for i, line in enumerate(contents) for j, cell in enumerate(line) if cell == 'A'][0]
        self.goal = [(i, j) for i, line in enumerate(contents) for j, cell in enumerate(line) if cell == 'B'][0]

        self.solution = None
        self.player_pos = self.start
        self.num_explored = 0
        self.solution_found = False
        self.explored = set() 
        self.frontier_nodes = []

    def neighbors(self, state):
        """Devuelve los vecinos válidos de un estado en el laberinto."""
        row, col = state
        candidates = [("up", (row - 1, col)), ("down", (row + 1, col)), ("left", (row, col - 1)), ("right", (row, col + 1))]
        return [(action, (r, c)) for action, (r, c) in candidates if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]]

    def step(self, frontier):
        """Realiza un paso en el proceso de resolución del laberinto, explorando un nodo.
        Devuelve True si encontró la solución; de lo contrario, False.
        """
        if not frontier.empty():
            node = frontier.remove()
            self.num_explored += 1

            if node.state == self.goal:
                actions, cells = [], []
                while node.parent:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse(), cells.reverse()
                self.solution = (actions, cells)
                self.solution_found = True
                return True

            self.explored.add(node.state)

            self.frontier_nodes.clear()
            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    child = Node(state=state, parent=node, action=action)
                    frontier.add(child)
                    self.frontier_nodes.append(child)

        return False

    def solve(self, frontier):
        """Inicia el proceso de resolución del laberinto con la estructura de frontera dada (pila o cola).
        """
        self.num_explored = 0
        start = Node(state=self.start, parent=None, action=None)
        frontier.add(start)
        self.explored = set()
        self.solution_found = False
        self.solution = None
        self.frontier_nodes = []
    
    def solve_dfs(self):
        """Resuelve el laberinto utilizando búsqueda por profundidad."""
        return self.solve(StackFrontier())

    def solve_bfs(self):
        """Resuelve el laberinto utilizando búsqueda por amplitud."""
        return self.solve(QueueFrontier())
    
    def solve_greedy(self):
        """Resuelve el laberinto utilizando búsqueda Greedy (Codiciosa)."""
        frontier = GreedyFrontier(self.goal)
        self.solve(frontier)

    def solve_a_star(self):
        """Resuelve el laberinto utilizando el algoritmo A*."""
        frontier = AStarFrontier(self.start, self.goal)
        self.solve(frontier)

    def move_player(self, direction):
        """Mueve al jugador en la dirección especificada si es una posición válida."""
        row, col = self.player_pos
        new_pos = {
            "up": (row - 1, col),
            "down": (row + 1, col),
            "left": (row, col - 1),
            "right": (row, col + 1)
        }.get(direction)
        if new_pos and 0 <= new_pos[0] < self.height and 0 <= new_pos[1] < self.width and not self.walls[new_pos[0]][new_pos[1]]:
            self.player_pos = new_pos


def calculate_cell_size(maze):
    cell_width, cell_height = SCREEN_WIDTH // maze.width, (SCREEN_HEIGHT - NAVBAR_HEIGHT) // maze.height
    return min(cell_width, cell_height)

def draw_maze(screen, maze, cell_size, images, show_solution=False):
    wall_img, path_img, start_img, goal_img, step_img, player_img = (pygame.transform.scale(img, (cell_size, cell_size)) for img in images)
    maze_width_in_pixels = maze.width * cell_size
    maze_height_in_pixels = maze.height * cell_size
    offset_x = (SCREEN_WIDTH - maze_width_in_pixels) // 2
    offset_y = (SCREEN_HEIGHT - NAVBAR_HEIGHT - maze_height_in_pixels) // 2 + NAVBAR_HEIGHT

    for i, row in enumerate(maze.walls):
        for j, wall in enumerate(row):
            img = wall_img if wall else path_img
            screen.blit(img, (j * cell_size + offset_x, i * cell_size + offset_y))

    if show_solution and maze.solution:
        for cell in maze.solution[1]:
            screen.blit(step_img, (cell[1] * cell_size + offset_x, cell[0] * cell_size + offset_y))

    screen.blit(start_img, (maze.start[1] * cell_size + offset_x, maze.start[0] * cell_size + offset_y))
    screen.blit(goal_img, (maze.goal[1] * cell_size + offset_x, maze.goal[0] * cell_size + offset_y))
    screen.blit(player_img, (maze.player_pos[1] * cell_size + offset_x, maze.player_pos[0] * cell_size + offset_y))

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Laberinto Interactivo")
    
    images = [pygame.image.load(img) for img in ["wall.png", "path.png", "start.png", "goal.png", "step.png", "player.png"]]
    background_image = pygame.image.load("background.png")
    alert_image = pygame.image.load("alert.png")
    impossible_image = pygame.image.load("impossible.png")
    
    manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
    solve_selector = pygame_gui.elements.UIDropDownMenu(
        ['Búsqueda por Profundidad', 'Búsqueda por Amplitud', 'Greedy', 'A*'],
        'Búsqueda por Profundidad', relative_rect=pygame.Rect((10, 10), (200, 40)), manager=manager
    )
    maze_selector = pygame_gui.elements.UIDropDownMenu(['Fácil', 'Medio', "Dificil", "Muy Dificil", "Imposible"], 'Fácil', relative_rect=pygame.Rect((230, 10), (200, 40)), manager=manager)
    
    maze = Maze('laberinto.txt')
    cell_size = calculate_cell_size(maze)

    frontier = None
    solving = False
    solved = False
    num_explored = 0
    move_step = 0
    move_speed = 20
    clock = pygame.time.Clock()

    alert_start_time, alert_shown = None, False
    impossible_start_time, impossible_shown = None, False

    running = True
    while running:
        time_delta = clock.tick(30) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    direction = {pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right"}[event.key]
                    maze.move_player(direction)
                    alert_shown = False
                elif event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.USEREVENT and event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                if event.ui_element == solve_selector:
                    if event.text == 'Búsqueda por Profundidad':
                        frontier = StackFrontier()
                    elif event.text == 'Búsqueda por Amplitud':
                        frontier = QueueFrontier()
                    elif event.text == 'Greedy':
                        maze.solve_greedy()
                    elif event.text == 'A*':
                        maze.solve_a_star()

                    maze.solve(frontier)
                    solving = True
                    solved = False
                    move_step = 0

                elif event.ui_element == maze_selector:
                    if event.text == 'Fácil':
                        maze = Maze('laberinto.txt')
                    elif event.text == 'Medio':
                        maze = Maze('laberinto2.txt')
                    elif event.text == 'Dificil':
                        maze = Maze('laberinto3.txt')
                    elif event.text == 'Muy Dificil':
                        maze = Maze('laberinto4.txt')
                    elif event.text == 'Imposible':
                        maze = Maze('laberinto5.txt')
                    cell_size = calculate_cell_size(maze)
                    solving = False
                    solved = False
                    move_step = 0

            manager.process_events(event)
        
        screen.blit(background_image, (0, 0))
        draw_maze(screen, maze, cell_size, images, show_solution=solved)

        if solved:
            font = pygame.font.Font(None, 36)
            text = font.render(f"Estados explorados: {maze.num_explored}", True, (0, 0, 0))
            screen.blit(text, (SCREEN_WIDTH - 300, 20))

        manager.update(time_delta)
        manager.draw_ui(screen)

        maze_width_in_pixels = maze.width * cell_size
        maze_height_in_pixels = maze.height * cell_size
        offset_x = (SCREEN_WIDTH - maze_width_in_pixels) // 2
        offset_y = (SCREEN_HEIGHT - NAVBAR_HEIGHT - maze_height_in_pixels) // 2 + NAVBAR_HEIGHT

        if solving and not solved:
            solving = not maze.step(frontier)
            
            for node in maze.frontier_nodes:
                pygame.draw.rect(screen, (0, 255, 0), 
                    (node.state[1] * cell_size + offset_x, node.state[0] * cell_size + offset_y, cell_size, cell_size))
            
            for explored in maze.explored:
                pygame.draw.rect(screen, (255, 0, 0), 
                    (explored[1] * cell_size + offset_x, explored[0] * cell_size + offset_y, cell_size, cell_size))

        if maze.solution_found and move_step < len(maze.solution[1]):
            target_cell = maze.solution[1][move_step]
            if maze.player_pos != target_cell:
                maze.move_player(maze.solution[0][move_step])
            else:
                move_step += 1
            if move_step == len(maze.solution[1]):
                solved = True
        
        if maze.player_pos == maze.goal and not alert_shown:
            alert_start_time = pygame.time.get_ticks()
            alert_shown = True
        
        if alert_start_time:
            elapsed_time = pygame.time.get_ticks() - alert_start_time
            if elapsed_time <= 2000:
                screen.blit(pygame.transform.scale(alert_image, (400, 200)), (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
            else:
                alert_start_time = None

        pygame.display.flip()

    pygame.quit()



if __name__ == "__main__":
    main()
