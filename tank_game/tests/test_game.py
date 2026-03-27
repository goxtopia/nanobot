import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.game import TankGame, TANK_SPEED, BULLET_SPEED, TANK_COOLDOWN

def test_map_generation():
    game = TankGame()
    assert len(game.map_grid) == game.height
    assert len(game.map_grid[0]) == game.width

    # Check borders are walls
    assert game.map_grid[0][0] == 1
    assert game.map_grid[game.height-1][game.width-1] == 1

def test_add_remove_tank():
    game = TankGame()
    tank_id = "test_tank_1"
    game.add_tank(tank_id)

    assert tank_id in game.tanks
    assert game.tanks[tank_id].health == 3
    assert game.tanks[tank_id].active == True

    game.remove_tank(tank_id)
    assert tank_id not in game.tanks

def test_tank_movement():
    game = TankGame()
    tank_id = "test_tank_1"
    game.add_tank(tank_id)

    tank = game.tanks[tank_id]

    # Force empty map at center
    game.map_grid[10][10] = 0
    game.map_grid[11][10] = 0
    game.map_grid[9][10] = 0
    game.map_grid[10][9] = 0
    game.map_grid[10][11] = 0

    tank.x = 10.5
    tank.y = 10.5
    tank.dir_x = 0.0
    tank.dir_y = -1.0 # Facing up

    game.move_tank(tank_id, forward=1, turn=0)
    assert tank.y == 10.5 - TANK_SPEED
    assert tank.x == 10.5

def test_tank_shooting():
    game = TankGame()
    tank_id = "test_tank_1"
    game.add_tank(tank_id)

    # Shoot
    game.shoot_bullet(tank_id)
    assert len(game.bullets) == 1

    # Cooldown check
    game.shoot_bullet(tank_id)
    assert len(game.bullets) == 1 # Shouldn't shoot again immediately

    assert game.tanks[tank_id].cooldown == TANK_COOLDOWN

def test_bullet_movement_and_wall_collision():
    game = TankGame()
    tank_id = "test_tank_1"
    game.add_tank(tank_id)

    tank = game.tanks[tank_id]
    tank.x = 5.5
    tank.y = 5.5
    tank.dir_x = 1
    tank.dir_y = 0

    # Wall right next to tank
    game.map_grid[5][6] = 1

    game.shoot_bullet(tank_id)
    bullet = game.bullets[0]

    init_x = bullet.x

    # Update game loop
    for _ in range(5):
        game.update()

    assert bullet.bounces > 0 or not bullet.active

def test_fog_of_war():
    game = TankGame()
    tank_id = "test_tank_1"
    game.add_tank(tank_id)

    tank = game.tanks[tank_id]
    tank.x = 10.5
    tank.y = 10.5

    # Build wall around it
    for i in range(9, 13):
        game.map_grid[i][9] = 1
        game.map_grid[i][12] = 1
        game.map_grid[9][i] = 1
        game.map_grid[12][i] = 1

    state = game.get_state(pov_tank_id=tank_id)
    grid = state['grid']

    # Fog is represented by 2
    assert grid[20][20] == 2 # Outside wall is fog
    assert grid[10][10] != 2 # Inside wall is visible
