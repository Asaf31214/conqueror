import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Conqueror")


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRID_COLOR = (200, 200, 200)


TILE_SIZE = 40
GRID_WIDTH = WIDTH // TILE_SIZE
GRID_HEIGHT = HEIGHT // TILE_SIZE


clicked_tiles = []

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            tile_x, tile_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
            if (tile_x, tile_y) not in clicked_tiles:
                clicked_tiles.append((tile_x, tile_y))

    window.fill(WHITE)


    for x in range(0, WIDTH, TILE_SIZE):
        pygame.draw.line(window, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, TILE_SIZE):
        pygame.draw.line(window, GRID_COLOR, (0, y), (WIDTH, y))


    for tile_x, tile_y in clicked_tiles:
        pygame.draw.rect(
            window,
            (255, 0, 0),
            (tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        )
    
    pygame.display.flip()

pygame.quit()
sys.exit()
