from dataclasses import dataclass

import pygame
import asyncio
import pickle

import httpx

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


@dataclass
class Team:
    Player1 = "Player1"
    Player2 = "Player2"
    Bot = "Bot"


MAX_HP = 80


def get_rect(tile_x: int, tile_y: int, scale: float = 1.0) -> tuple:
    offset_x = TILE_SIZE * (1 - scale) / 2
    offset_y = TILE_SIZE * (1 - scale) / 2
    return (tile_x * TILE_SIZE + offset_x,
            tile_y * TILE_SIZE + offset_y,
            TILE_SIZE * scale,
            TILE_SIZE * scale)


class Tile:
    def __init__(self, x: int, y: int, team: str = Team.Bot):
        self._x = x
        self._y = y
        self._hp: float = MAX_HP
        self._team: str = team

    def get_coords(self):
        return self._x, self._y

    def get_color(self):
        return TEAM_COLORS[self._team]

    def get_hp(self):
        return self._hp


    def get_team(self):
        return self._team


class Board:
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tiles = [[Tile(x, y)
                       for y in range(grid_height)]
                      for x in range(grid_width)]


    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[x][y]

    def get_team_tiles(self, team: str) -> list[Tile]:
        return [self.tiles[x][y]
                for x in range(self.grid_width)
                for y in range(self.grid_height)
                if self.tiles[x][y].get_team() == team]


# MAIN EVENT HANDLER
async def event_handler(event: pygame.event):
    if event.type == pygame.QUIT:
        await handle_quit()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8000/event", json={'mouse_pos': [mouse_x, mouse_y]})


# Event handler functions
async def handle_quit():
    global running
    running = False

# DISPLAY RENDERER
def render(window: pygame.Surface):
    window.fill(WHITE)
    draw_tiles(window)
    draw_selections(window)
    draw_lines(window)
    display_message(window)
    pygame.display.flip()


def display_message(window: pygame.Surface, font_size: int = 30):
    font = pygame.font.SysFont('Comic Sans MS', font_size)
    line_height = font.get_height()

    turn_message = "Your Turn"
    text_surface = font.render(turn_message, True, BLACK)
    x_position = 16 if turn else WINDOW_WIDTH - 16 - text_surface.get_width()
    y_position = WINDOW_HEIGHT + 2 * line_height
    window.blit(text_surface, (x_position, y_position))

    player_1_score = len(board.get_team_tiles(Team.Player1))
    player_2_score = len(board.get_team_tiles(Team.Player2))
    text1_surface = font.render(f"{Team.Player1}: {player_1_score}", True, BLACK)
    text2_surface = font.render(f"{Team.Player2}: {player_2_score}", True, BLACK)
    y_position = WINDOW_HEIGHT + line_height
    x_1_position = 16
    x_2_position = WINDOW_WIDTH - 16 - text2_surface.get_width()
    window.blit(text1_surface, (x_1_position, y_position))
    window.blit(text2_surface, (x_2_position, y_position))

    manual_lines = message.split('\n')
    lines = []
    current_line = ""

    for line in manual_lines:
        lines.append(current_line)
        current_line = ""
        words = line.split(' ')
        for word in words:
            if font.size(current_line + word + " ")[0] > WINDOW_WIDTH - 20:
                lines.append(current_line)
                current_line = word + " "
            else:
                current_line += word + " "

    lines.append(current_line)

    for i, line in enumerate(lines):
        text_surface = font.render(line.strip(), True, BLACK)
        x_position = (WINDOW_WIDTH - 32) // 2 - text_surface.get_width() // 2
        y_position = WINDOW_HEIGHT + (i + 4) * line_height
        window.blit(text_surface, (x_position, y_position))


def draw_lines(window: pygame.Surface):
    for x in x_borders:
        pygame.draw.line(window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in y_borders:
        pygame.draw.line(window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))


def draw_tiles(window: pygame.Surface):
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
    for tile in click_queue:
        pygame.draw.rect(
            surface=window,
            color=GREEN,
            rect=get_rect(*tile.get_coords()),
            width=5
        )


running: bool = True
turn = True
click_queue: list = []
message = 'Start the game by clicking on two tiles! '

board: Board


async def get_board():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/board")
        global board
        board = pickle.loads(response.content)

async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/data")
        data = response.json()
        global message
        global turn
        message = data['message']
        turn = data['turn']

async def get_queue():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/queue")
        global click_queue
        click_queue = pickle.loads(response.content)

async def main():
    pygame.init()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + 250))
    pygame.display.set_caption("Conqueror")

    global running
    while running:
        await asyncio.gather(
            *[asyncio.create_task(event_handler(event))
              for event in pygame.event.get()],
            get_board(),
            get_data(),
            get_queue()
        )
        render(window)
        await asyncio.sleep(0.01)  # 100 Tick rate
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
