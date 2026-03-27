import math
import random
from typing import List, Dict, Tuple, Optional

# Constants
GRID_SIZE = 40  # 40x40 grid map
CELL_SIZE = 1   # Logical size
TANK_RADIUS = 0.4
BULLET_RADIUS = 0.1
BULLET_SPEED = 0.5
TANK_SPEED = 0.2
TANK_COOLDOWN = 30 # Ticks before shooting again
MAX_BOUNCES = 1

class Bullet:
    def __init__(self, id: str, owner_id: str, x: float, y: float, dir_x: float, dir_y: float):
        self.id = id
        self.owner_id = owner_id
        self.x = x
        self.y = y
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.bounces = 0
        self.active = True

class Tank:
    def __init__(self, id: str, x: float, y: float):
        self.id = id
        self.x = x
        self.y = y
        self.dir_x = 0.0
        self.dir_y = -1.0
        self.cooldown = 0
        self.health = 3
        self.active = True

class TankGame:
    def __init__(self):
        self.width = GRID_SIZE
        self.height = GRID_SIZE
        self.map_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.tanks: Dict[str, Tank] = {}
        self.bullets: List[Bullet] = []
        self.bullet_counter = 0
        self.generate_map()

    def generate_map(self):
        """Generates a map with 3 random variations (Empty, Obstacles, Dense/Maze)."""
        map_type = random.choice(['empty', 'obstacles', 'dense'])
        self.map_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]

        # Borders are always walls
        for x in range(self.width):
            self.map_grid[0][x] = 1
            self.map_grid[self.height - 1][x] = 1
        for y in range(self.height):
            self.map_grid[y][0] = 1
            self.map_grid[y][self.width - 1] = 1

        if map_type == 'empty':
            # Just few random blocks
            self._add_random_blocks(10)
        elif map_type == 'obstacles':
            # Some structured blocks
            for _ in range(15):
                rx = random.randint(2, self.width - 5)
                ry = random.randint(2, self.height - 5)
                for w in range(3):
                    for h in range(3):
                        if random.random() > 0.2:
                            self.map_grid[ry+h][rx+w] = 1
        elif map_type == 'dense':
            # Dense / symmetric maze-like
            for y in range(2, self.height - 2, 2):
                for x in range(2, self.width - 2, 2):
                    if random.random() > 0.3:
                        self.map_grid[y][x] = 1
                        if random.random() > 0.5:
                            self.map_grid[y+1][x] = 1
                        else:
                            self.map_grid[y][x+1] = 1

    def _add_random_blocks(self, num_blocks):
        for _ in range(num_blocks):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            self.map_grid[y][x] = 1

    def is_wall(self, x: int, y: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.map_grid[y][x] == 1
        return True # Out of bounds is a wall

    def get_spawn_point(self) -> Tuple[float, float]:
        for _ in range(100):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)
            if not self.is_wall(x, y):
                # Ensure no other tank is too close
                conflict = False
                for t in self.tanks.values():
                    if t.active and math.hypot(t.x - x, t.y - y) < 2.0:
                        conflict = True
                        break
                if not conflict:
                    return float(x) + 0.5, float(y) + 0.5
        return 1.5, 1.5

    def add_tank(self, tank_id: str):
        x, y = self.get_spawn_point()
        self.tanks[tank_id] = Tank(tank_id, x, y)

    def remove_tank(self, tank_id: str):
        if tank_id in self.tanks:
            del self.tanks[tank_id]

    def calculate_fov(self, origin_x: float, origin_y: float, radius: int = 15) -> List[List[bool]]:
        """Calculates Field of View using raycasting (Fog of War)."""
        visible = [[False for _ in range(self.width)] for _ in range(self.height)]

        ox_int, oy_int = int(origin_x), int(origin_y)
        if 0 <= ox_int < self.width and 0 <= oy_int < self.height:
            visible[oy_int][ox_int] = True

        # Raycast in 360 degrees
        num_rays = 360
        for i in range(num_rays):
            angle = math.radians(i)
            dx = math.cos(angle)
            dy = math.sin(angle)

            rx, ry = origin_x, origin_y
            for step in range(radius * 2): # Steps of 0.5 size
                rx += dx * 0.5
                ry += dy * 0.5

                grid_x, grid_y = int(rx), int(ry)
                if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                    visible[grid_y][grid_x] = True
                    if self.map_grid[grid_y][grid_x] == 1:
                        # Wall blocks further vision
                        break
                else:
                    break

        return visible

    def move_tank(self, tank_id: str, forward: int, turn: int):
        if tank_id not in self.tanks:
            return
        tank = self.tanks[tank_id]
        if not tank.active:
            return

        if turn != 0:
            angle = math.atan2(tank.dir_y, tank.dir_x)
            angle += math.radians(10 * turn)
            tank.dir_x = math.cos(angle)
            tank.dir_y = math.sin(angle)

        if forward != 0:
            nx = tank.x + tank.dir_x * TANK_SPEED * forward
            ny = tank.y + tank.dir_y * TANK_SPEED * forward

            if not self.check_collision(nx, tank.y, TANK_RADIUS, ignore_tank_id=tank_id):
                tank.x = nx
            if not self.check_collision(tank.x, ny, TANK_RADIUS, ignore_tank_id=tank_id):
                tank.y = ny

    def check_collision(self, x: float, y: float, radius: float, ignore_tank_id: str = None) -> bool:
        """Check collision with walls and other tanks."""
        min_x, max_x = int(x - radius), int(x + radius)
        min_y, max_y = int(y - radius), int(y + radius)

        for cy in range(min_y, max_y + 1):
            for cx in range(min_x, max_x + 1):
                if 0 <= cx < self.width and 0 <= cy < self.height:
                    if self.map_grid[cy][cx] == 1:
                        # Circle-Rectangle collision approx
                        closest_x = max(cx, min(x, cx + 1))
                        closest_y = max(cy, min(y, cy + 1))
                        dist_x = x - closest_x
                        dist_y = y - closest_y
                        if (dist_x**2 + dist_y**2) < radius**2:
                            return True
                else:
                    return True # Bounds

        # Check tank collisions
        for tid, t in self.tanks.items():
            if t.active and tid != ignore_tank_id:
                dist = math.hypot(t.x - x, t.y - y)
                if dist < radius * 2:
                    return True

        return False

    def shoot_bullet(self, tank_id: str):
        if tank_id not in self.tanks:
            return
        tank = self.tanks[tank_id]
        if tank.cooldown <= 0 and tank.active:
            bx = tank.x + tank.dir_x * (TANK_RADIUS + BULLET_RADIUS + 0.1)
            by = tank.y + tank.dir_y * (TANK_RADIUS + BULLET_RADIUS + 0.1)
            b_id = f"b_{self.bullet_counter}"
            self.bullet_counter += 1
            self.bullets.append(Bullet(b_id, tank.id, bx, by, tank.dir_x, tank.dir_y))
            tank.cooldown = TANK_COOLDOWN

    def update(self):
        """Update game logic for one tick."""
        # Cool downs
        for t in self.tanks.values():
            if t.cooldown > 0:
                t.cooldown -= 1

        # Move bullets
        for b in self.bullets:
            if not b.active:
                continue

            nx = b.x + b.dir_x * BULLET_SPEED
            ny = b.y + b.dir_y * BULLET_SPEED

            # Wall Collision / Bouncing
            bounced = False

            grid_x, grid_y = int(nx), int(ny)
            if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
                if self.map_grid[grid_y][grid_x] == 1:
                    b.bounces += 1
                    bounced = True
                    if b.bounces > MAX_BOUNCES:
                        b.active = False
                    else:
                        # Simple bounce reflection
                        if int(b.x) != grid_x:
                            b.dir_x *= -1
                        if int(b.y) != grid_y:
                            b.dir_y *= -1
                        nx = b.x + b.dir_x * BULLET_SPEED
                        ny = b.y + b.dir_y * BULLET_SPEED
            else:
                b.active = False # Out of bounds

            b.x, b.y = nx, ny

            if b.active:
                # Tank collision
                for t in self.tanks.values():
                    if t.active and t.id != b.owner_id:
                        dist = math.hypot(t.x - b.x, t.y - b.y)
                        if dist < (TANK_RADIUS + BULLET_RADIUS):
                            b.active = False
                            t.health -= 1
                            if t.health <= 0:
                                t.active = False
                                # Respawn after a delay handled by main loop or simply respawn
                            break

        self.bullets = [b for b in self.bullets if b.active]

    def reset_tank(self, tank_id: str):
        if tank_id in self.tanks:
            x, y = self.get_spawn_point()
            self.tanks[tank_id].x = x
            self.tanks[tank_id].y = y
            self.tanks[tank_id].health = 3
            self.tanks[tank_id].active = True

    def get_state(self, pov_tank_id: Optional[str] = None) -> Dict:
        """Get game state, optionally masked by Fog of War."""
        tanks_state = {}
        bullets_state = []

        fov = None
        if pov_tank_id and pov_tank_id in self.tanks:
            t = self.tanks[pov_tank_id]
            if t.active:
                fov = self.calculate_fov(t.x, t.y)

        # Apply Fog of War
        for tid, t in self.tanks.items():
            if t.active:
                if fov is None or (0 <= int(t.y) < self.height and 0 <= int(t.x) < self.width and fov[int(t.y)][int(t.x)]):
                    tanks_state[tid] = {
                        "x": t.x, "y": t.y,
                        "dir_x": t.dir_x, "dir_y": t.dir_y,
                        "hp": t.health,
                        "visible": True
                    }

        for b in self.bullets:
            if b.active:
                if fov is None or (0 <= int(b.y) < self.height and 0 <= int(b.x) < self.width and fov[int(b.y)][int(b.x)]):
                    bullets_state.append({
                        "x": b.x, "y": b.y, "owner": b.owner_id
                    })

        state = {
            "tanks": tanks_state,
            "bullets": bullets_state,
            "grid": self.map_grid if fov is None else self._mask_grid(fov),
            "width": self.width,
            "height": self.height
        }
        return state

    def _mask_grid(self, fov: List[List[bool]]) -> List[List[int]]:
        masked = [[2 for _ in range(self.width)] for _ in range(self.height)] # 2 = fog
        for y in range(self.height):
            for x in range(self.width):
                if fov[y][x]:
                    masked[y][x] = self.map_grid[y][x]
        return masked
