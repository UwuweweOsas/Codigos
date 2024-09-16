import pygame
import pygame_gui
from collections import deque

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

class Maze:
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()

        if contents.count("A") != 1 or contents.count("B") != 1:
            raise Exception("maze must have exactly one start point and one goal")

        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)

        self.walls = [[True if cell != ' ' and cell != 'A' and cell != 'B' else False for cell in line] for line in contents]
        self.start = [(i, j) for i, line in enumerate(contents) for j, cell in enumerate(line) if cell == 'A'][0]
        self.goal = [(i, j) for i, line in enumerate(contents) for j, cell in enumerate(line) if cell == 'B'][0]

        self.solution = None
        self.player_pos = self.start

    def neighbors(self, state):
        row, col = state
        candidates = [("up", (row - 1, col)), ("down", (row + 1, col)), ("left", (row, col - 1)), ("right", (row, col + 1))]
        return [(action, (r, c)) for action, (r, c) in candidates if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]]

    def solve(self, frontier):
        self.num_explored = 0
        start = Node(state=self.start, parent=None, action=None)
        frontier.add(start)
        self.explored = set()

        while not frontier.empty():
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
                return True

            self.explored.add(node.state)
            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    frontier.add(Node(state=state, parent=node, action=action))

        return False

    def solve_dfs(self):
        return self.solve(StackFrontier())

    def solve_bfs(self):
        return self.solve(QueueFrontier())

    def move_player(self, direction):
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
    solve_selector = pygame_gui.elements.UIDropDownMenu(['Búsqueda por Profundidad', 'Búsqueda por Amplitud'], 'Búsqueda por Profundidad', relative_rect=pygame.Rect((10, 10), (200, 40)), manager=manager)
    maze_selector = pygame_gui.elements.UIDropDownMenu(['Fácil', 'Medio', "Dificil", "Muy Dificil", "Imposible"], 'Fácil', relative_rect=pygame.Rect((230, 10), (200, 40)), manager=manager)

    maze = Maze('laberinto.txt')
    cell_size = calculate_cell_size(maze)

    clock = pygame.time.Clock()
    solved, num_explored = False, 0
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
                        solved = maze.solve_dfs()
                    else:
                        solved = maze.solve_bfs()
                    
                    if solved:
                        num_explored = maze.num_explored
                        solved = True
                        impossible_shown = False
                    else:
                        impossible_start_time = pygame.time.get_ticks()
                        impossible_shown = True

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
                    solved = False
                    impossible_shown = False

            manager.process_events(event)

        screen.blit(background_image, (0, 0))
        draw_maze(screen, maze, cell_size, images, show_solution=solved)

        if solved:
            font = pygame.font.Font(None, 36)
            text = font.render(f"Estados explorados: {num_explored}", True, (0, 0, 0))
            screen.blit(text, (SCREEN_WIDTH - 300, 20))

        manager.update(time_delta)
        manager.draw_ui(screen)

        if impossible_start_time:
            elapsed_time = pygame.time.get_ticks() - impossible_start_time
            if elapsed_time <= 2000:
                screen.blit(pygame.transform.scale(impossible_image, (400, 200)), (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))
            else:
                impossible_start_time = None
                impossible_shown = False

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
