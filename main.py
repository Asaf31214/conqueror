from dataclasses import dataclass
import random

import pygame
import asyncio

from queue import Queue

WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRID_COLOR = (200, 200, 200)

TILE_SIZE = 60
GRID_WIDTH = WINDOW_WIDTH // TILE_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // TILE_SIZE

x_borders = range(0, WINDOW_WIDTH, TILE_SIZE)
y_borders = range(0, WINDOW_HEIGHT, TILE_SIZE)

TEAM_COLORS = {"Player1": BLUE, "Player2": RED, "Bot": GRID_COLOR}

DAMAGE_MODIFIERS = {("Player1", "Bot"): 1.0,
                    ("Player2", "Bot"): 1.0,
                    ("Bot", "Player1"): 0.5,
                    ("Bot", "Player2"): 0.5,
                    ("Bot", "Bot"): 0.0,
                    ("Player1", "Player1"): 0.0,
                    ("Player2", "Player2"): 0.0,
                    ("Player1", "Player2"): 2.0,
                    ("Player2", "Player1"): 2.0,}

@dataclass
class Team:
    Player1= "Player1"
    Player2= "Player2"
    Bot= "Bot"

MAX_HP = 80


def get_rect(tile_x: int, tile_y: int, scale: float = 1.0) -> tuple:
    offset_x = TILE_SIZE * (1-scale) / 2
    offset_y = TILE_SIZE * (1-scale) / 2
    return (tile_x * TILE_SIZE + offset_x,
            tile_y * TILE_SIZE + offset_y,
            TILE_SIZE * scale,
            TILE_SIZE * scale)

def is_adjacent(tile_1: "Tile", tile_2: "Tile") -> bool:
    tile_1_x, tile_1_y = tile_1.get_coords()
    tile_2_x, tile_2_y = tile_2.get_coords()
    return abs(tile_1_x - tile_2_x) + abs(tile_1_y - tile_2_y) == 1


def flip_coin():
    return random.choice([True, False])


class Tile:
    def __init__(self, x: int, y: int, team: str = Team.Bot):
        self._x = x
        self._y = y
        self._hp: float = MAX_HP
        self._team: str = team
        self._has_attacked: bool = False

    def get_coords(self):
        return self._x, self._y

    def get_color(self):
        return TEAM_COLORS[self._team]

    def get_hp(self):
        return self._hp

    def _set_hp(self, hp: float):
        self._hp = max(0.0, min(hp, MAX_HP))
        if self._hp <= 10:
            self._hp = 0

    def switch_team(self, team: str):
        self._hp = MAX_HP
        self._team = team

    def get_team(self):
        return self._team

    def receive_attack(self, attacker: "Tile" = None):
        damage_modifier = DAMAGE_MODIFIERS[(attacker._team, self._team)]
        damage = (self._hp / 2) * damage_modifier
        self._set_hp(self._hp - damage)
        if self._hp == 0:
            self.switch_team(attacker._team)


    def first_attack(self):
        if self._team != Team.Bot:
            if not self._has_attacked:
                self._has_attacked = True
                return True
        return False


class Board:
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tiles = [[Tile(x, y)
                       for y in range(grid_height)]
                      for x in range(grid_width)]

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        self.tiles[x][y] = tile

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[x][y]

    def get_team_power(self, tile: Tile) -> int:
        team = tile.get_team()
        if team == Team.Bot:
            x, y = tile.get_coords()
            x_to_center, y_to_center = (abs(x - (GRID_WIDTH-1) / 2),abs(y - (GRID_HEIGHT-1) / 2))
            if x_to_center > 2 and y_to_center > 2:
                return 1
            else:
                return 2
        return len([self.tiles[x][y]
                for x in range(self.grid_width)
                for y in range(self.grid_height)
                if self.tiles[x][y].get_team() == team])


def decide_winner(board: Board, attacker: Tile, attacked: Tile):
    if attacker.first_attack():
        return True
    attacker_team_power = board.get_team_power(attacker)
    attacked_team_power = board.get_team_power(attacked)

    attacker_hp = attacker.get_hp()
    attacked_hp = attacked.get_hp()

    attacker_chance = attacker_team_power * attacker_hp
    attacked_chance = attacked_team_power * attacked_hp
    print(attacker_chance, attacked_chance)

    return random.uniform(0, attacker_chance + attacked_chance) < attacker_chance


# MAIN EVENT HANDLER
async def event_handler(event: pygame.event, board: Board, window: pygame.Surface):
    if event.type == pygame.QUIT:
        await handle_quit()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        await handle_click(event, board, window)


# Event handler functions
async def handle_quit():
    global running
    running = False


async def handle_click(event: pygame.event, board: Board, window: pygame.Surface):
    mouse_x, mouse_y = event.pos
    tile_x, tile_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
    tile = board.get_tile(tile_x, tile_y)
    click_queue.put(tile)
    if click_queue.full():
        render(window, board)
        await asyncio.sleep(0.6)
        attacker = click_queue.get()
        attacked = click_queue.get()
        success = decide_winner(board, attacker, attacked)
        if not success:
            attacker, attacked = attacked, attacker
        if is_adjacent(attacker, attacked):
            attacked.receive_attack(attacker=attacker)



# DISPLAY RENDERER
def render(window: pygame.Surface, board: Board):
    window.fill(WHITE)
    draw_tiles(window, board)
    draw_selections(window)
    draw_lines(window)
    pygame.display.flip()


def draw_lines(window: pygame.Surface):
    for x in x_borders:
        pygame.draw.line(window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in y_borders:
        pygame.draw.line(window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))


def draw_tiles(window: pygame.Surface, board: Board):
    for tile_x in range(board.grid_width):
        for tile_y in range(board.grid_height):
            tile = board.get_tile(tile_x, tile_y)
            scale = tile.get_hp() / 100

            pygame.draw.rect(
                surface=window,
                color=tile.get_color(),
                rect=get_rect(tile_x, tile_y, scale),
            )

def draw_selections(window: pygame.Surface):
    selected_tiles = list(click_queue.queue)
    for tile in selected_tiles:
        pygame.draw.rect(
            surface=window,
            color=GREEN,
            rect=get_rect(*tile.get_coords()),
            width=5
        )

running: bool = True
click_queue: Queue[Tile] = Queue(maxsize=2)

async def main():
    pygame.init()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    board = Board(GRID_WIDTH, GRID_HEIGHT)

    player_1_base = Tile(0, 0, Team.Player1)
    player_2_base = Tile(GRID_WIDTH-1, GRID_HEIGHT-1, Team.Player2)
    board.set_tile(0, 0, player_1_base)
    board.set_tile(GRID_WIDTH-1, GRID_HEIGHT-1, player_2_base)

    pygame.display.set_caption("Conqueror")

    global running
    while running:
        await asyncio.gather(
            *[asyncio.create_task(event_handler(event, board, window))
              for event in pygame.event.get()])
        render(window, board)
        await asyncio.sleep(0.01) # 100 Tick rate
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
