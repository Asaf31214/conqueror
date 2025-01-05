from dataclasses import dataclass
import random

import pygame
import asyncio
import pickle

from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn

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
                    ("Player2", "Player1"): 2.0, }


@dataclass
class Team:
    Player1 = "Player1"
    Player2 = "Player2"
    Bot = "Bot"


MAX_HP = 80


def is_adjacent(tile_1: "Tile", tile_2: "Tile") -> bool:
    attack_range = 2 if len(board.get_team_tiles(tile_1.get_team())) >= 35 else 1
    tile_1_x, tile_1_y = tile_1.get_coords()
    tile_2_x, tile_2_y = tile_2.get_coords()
    return abs(tile_1_x - tile_2_x) + abs(tile_1_y - tile_2_y) <= attack_range



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

    def _set_hp(self, hp: float):
        self._hp = max(0.0, min(hp, MAX_HP))
        if self._hp <= 10:
            self._hp = 0

    def swap(self, other: "Tile"):
        self._hp, other._hp = other._hp, self._hp

    def switch_team(self, team: str):
        self._hp = MAX_HP
        self._team = team

    def get_team(self):
        return self._team

    def receive_attack(self, attacker: "Tile" = None) -> None:
        damage_modifier = DAMAGE_MODIFIERS[(attacker._team, self._team)]
        damage = (self._hp / 2) * damage_modifier
        self._set_hp(self._hp - damage)
        if self._hp == 0:
            set_message(new_message=f'{attacker} captured {self}!', append=True)
            self.switch_team(attacker._team)
            return

    def first_attack(self):
        if self._team != Team.Bot:
            if not has_attacked[self._team]:
                has_attacked[self._team] = True
                return True
        return False

    def __str__(self):
        return f"{self._team} ({self._x}, {self._y})"


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

    def get_team_tiles(self, team: str) -> list[Tile]:
        return [self.tiles[x][y]
                for x in range(self.grid_width)
                for y in range(self.grid_height)
                if self.tiles[x][y].get_team() == team]

    @classmethod
    def _attrition_modifier(cls, tile: Tile) -> float:
        player1_region = [(x, y) for x in range(GRID_WIDTH // 2) for y in range(GRID_HEIGHT // 2)]
        player2_region = [(x, y) for x in range(GRID_WIDTH // 2, GRID_WIDTH) for y in
                          range(GRID_HEIGHT // 2, GRID_HEIGHT)]
        if tile.get_coords() in player1_region:
            return 1.6 if tile.get_team() == Team.Player1 else 0.625
        if tile.get_coords() in player2_region:
            return 1.6 if tile.get_team() == Team.Player2 else 0.625
        return 1.0

    def get_team_power(self, tile: Tile) -> float:
        team = tile.get_team()
        if team == Team.Bot:
            x, y = tile.get_coords()
            x_to_center, y_to_center = (
                abs(x - (GRID_WIDTH - 1) / 2), abs(y - (GRID_HEIGHT - 1) / 2))
            if x_to_center > 2 and y_to_center > 2:
                return 1
            elif x_to_center > 1 and y_to_center > 1:
                return 2
            else:
                return 3
        return len(self.get_team_tiles(team)) * self._attrition_modifier(tile)

    def get_winner(self):
        team_1_alive = any(self.get_team_tiles(Team.Player1))
        team_2_alive = any(self.get_team_tiles(Team.Player2))
        if team_1_alive and team_2_alive:
            return None
        else:
            return Team.Player1 if team_1_alive else Team.Player2


def get_turn():
    return Team.Player1 if turn else Team.Player2


def switch_turn():
    global turn
    turn = not turn


def decide_winner(attacker: Tile, attacked: Tile):
    if attacker.first_attack():
        set_message(f'{attacker} wins the first attack!')
        return True
    attacker_team_power = board.get_team_power(attacker)
    attacked_team_power = board.get_team_power(attacked)

    attacker_hp = attacker.get_hp()
    attacked_hp = attacked.get_hp()

    attacker_chance = attacker_team_power * attacker_hp
    attacked_chance = attacked_team_power * attacked_hp
    winner = random.uniform(0, attacker_chance + attacked_chance) < attacker_chance
    set_message(
        f'{attacker} net power: {attacker_chance:.2f}, {attacked} net power: {attacked_chance:.2f}')
    if winner:
        set_message(
            new_message=f'{attacker} wins with {attacker_chance / (attacker_chance + attacked_chance) * 100:.2f}% chance!',
            append=True)
    else:
        set_message(
            new_message=f'{attacked} wins with {attacked_chance / (attacker_chance + attacked_chance) * 100:.2f}% chance!',
            append=True)
    return winner


def set_message(new_message: str, append: bool = False):
    global message
    if append:
        message += f'\n{new_message}'
    else:
        message = new_message
    return message


# MAIN EVENT HANDLER
async def event_handler(event: pygame.event):
    await handle_click(event)


# Event handler functions
async def handle_quit():
    global running
    running = False


async def handle_click(event):
    if board.get_winner():
        set_message(f'Game over! Winner: {board.get_winner()}')
        return
    mouse_x, mouse_y = event
    if mouse_x > WINDOW_WIDTH or mouse_y > WINDOW_HEIGHT:
        return
    tile_x, tile_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
    tile = board.get_tile(tile_x, tile_y)
    click_queue.append(tile)
    if len(click_queue) == 2:
        attacker, attacked = click_queue
        if attacker == attacked or attacker.get_team() == Team.Bot:
            click_queue.clear()
            return
        if get_turn() != attacker.get_team():
            click_queue.clear()
            set_message('Not your turn!')
            return
        if is_adjacent(attacker, attacked):
            await asyncio.sleep(0.5)
            if attacker.get_team() == attacked.get_team():
                attacker.swap(attacked)
                set_message(f'{attacker.get_team()} swapped tiles {attacker} and {attacked}!')
            else:
                success = decide_winner(attacker, attacked)
                if not success:
                    attacker, attacked = attacked, attacker
                capture = attacked.receive_attack(attacker=attacker)
                if capture:
                    set_message(new_message=capture, append=True)
                if board.get_winner():
                    set_message(f'Game over! Winner: {board.get_winner()}')
            switch_turn()
        click_queue.clear()




running: bool = True
turn = True
click_queue: list = []
message = 'Start the game by clicking on two tiles! '
has_attacked = {"Player1": False, "Player2": False}

server_events = []


def get_events():
    global server_events
    events = server_events[:]
    server_events.clear()
    return events

board: Board

async def main():
    pygame.init()
    global board
    board = Board(GRID_WIDTH, GRID_HEIGHT)

    player_1_base = Tile(0, 0, Team.Player1)
    player_2_base = Tile(GRID_WIDTH - 1, GRID_HEIGHT - 1, Team.Player2)
    board.set_tile(0, 0, player_1_base)
    board.set_tile(GRID_WIDTH - 1, GRID_HEIGHT - 1, player_2_base)

    pygame.display.set_caption("Conqueror")

    global running
    while running:
        await asyncio.gather(
            *[asyncio.create_task(event_handler(event))
              for event in get_events()])
        await asyncio.sleep(0.01)  # 100 Tick rate
    pygame.quit()


async def server():
    app = FastAPI()

    @app.post("/event")
    async def receive_event(request: Request):
        global server_events
        data = await request.json()
        event = data['mouse_pos']
        server_events.append(event)
        return

    @app.get("/board")
    async def get_board():
        global board
        pickled_board = pickle.dumps(board)
        return Response(content=pickled_board, media_type="application/octet-stream")

    @app.get("/queue")
    async def get_queue():
        global click_queue
        pickled_queue = pickle.dumps(click_queue)
        return Response(content=pickled_queue, media_type="application/octet-stream")

    @app.get("/data")
    async def get_data():
        global message
        global has_attacked
        global turn
        return {"message": message, "turn": turn, "has_attacked": has_attacked}

    config = uvicorn.Config(app, host="127.0.0.1", port=8000)
    server_ = uvicorn.Server(config)

    await server_.serve()


async def run():
    await asyncio.gather(
        main(),
        server()
    )


if __name__ == "__main__":
    asyncio.run(run())
