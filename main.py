import pygame
import asyncio

WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRID_COLOR = (200, 200, 200)

TILE_SIZE = 60
GRID_WIDTH = WINDOW_WIDTH // TILE_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // TILE_SIZE


class Tile:
    def __init__(self, x: int, y: int, is_flipped: bool = False):
        self.x = x
        self.y = y
        self.is_flipped = is_flipped


class Board:
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tiles = [[Tile(x, y) for y in range(grid_height)] for x in range(grid_width)]

    def set_tile(self, x: int, y: int, tile: Tile) -> None:
        self.tiles[x][y] = tile

    def get_tile(self, x: int, y: int) -> Tile:
        return self.tiles[x][y]


# MAIN EVENT HANDLER
async def event_handler(event: pygame.event.Event, clicked_tiles: list[tuple[int, int]]):
    if event.type == pygame.QUIT:
        await handle_quit()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        await handle_click(event, clicked_tiles)


# Event handler functions
async def handle_quit():
    global running
    running = False


async def handle_click(event: pygame.event.Event, clicked_tiles: list[tuple[int, int]]):
    mouse_x, mouse_y = event.pos
    tile_x, tile_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
    if (tile_x, tile_y) not in clicked_tiles:
        clicked_tiles.append((tile_x, tile_y))


# DISPLAY RENDERER
def render(window: pygame.Surface, clicked_tiles: list[tuple[int, int]]):
    window.fill(WHITE)
    draw_lines(window)
    for tile_x, tile_y in clicked_tiles:
        pygame.draw.rect(
            surface=window,
            color=RED,
            rect=(tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        )
    pygame.display.flip()

def draw_lines(window: pygame.Surface):
    for x in range(0, WINDOW_WIDTH, TILE_SIZE):
        pygame.draw.line(window, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, TILE_SIZE):
        pygame.draw.line(window, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

running: bool = True


async def main():
    # Game initiation
    pygame.init()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    board = Board(GRID_WIDTH, GRID_HEIGHT)

    pygame.display.set_caption("Conqueror")

    clicked_tiles = []
    global running
    while running:
        events = pygame.event.get()
        tasks = [asyncio.create_task(event_handler(event, clicked_tiles)) for event in events]
        await asyncio.gather(*tasks)

        render(window, clicked_tiles)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
