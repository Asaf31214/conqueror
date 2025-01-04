import pygame
import asyncio

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


def get_rect(tile_x: int, tile_y: int, scale: float = 1.0) -> tuple:
    offset_x = TILE_SIZE * (1-scale) / 2
    offset_y = TILE_SIZE * (1-scale) / 2
    return (tile_x * TILE_SIZE + offset_x,
            tile_y * TILE_SIZE + offset_y,
            TILE_SIZE * scale,
            TILE_SIZE * scale)


class Tile:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.hp: float = 100

    def get_coords(self):
        return self.x, self.y


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


# MAIN EVENT HANDLER
async def event_handler(event: pygame.event, board: Board):
    if event.type == pygame.QUIT:
        await handle_quit()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        await handle_click(event, board)


# Event handler functions
async def handle_quit():
    global running
    running = False


async def handle_click(event: pygame.event, board: Board):
    mouse_x, mouse_y = event.pos
    tile_x, tile_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
    pass


# DISPLAY RENDERER
def render(window: pygame.Surface, board: Board):
    window.fill(WHITE)
    draw_tiles(window, board)
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
            scale = tile.hp / 100
            pygame.draw.rect(
                surface=window,
                color=GREEN,
                rect=get_rect(tile_x, tile_y, scale),
            )



running: bool = True


async def main():
    pygame.init()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    board = Board(GRID_WIDTH, GRID_HEIGHT)

    pygame.display.set_caption("Conqueror")

    global running
    while running:
        await asyncio.gather(
            *[asyncio.create_task(event_handler(event, board))
              for event in pygame.event.get()])
        render(window, board)
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
