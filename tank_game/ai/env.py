import gymnasium as gym
from gymnasium import spaces
import numpy as np
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.game import TankGame

class TankEnv(gym.Env):
    """Custom Environment that follows gym interface"""
    metadata = {'render_modes': ['human'], "render_fps": 30}

    def __init__(self, render_mode=None):
        super(TankEnv, self).__init__()
        self.game = TankGame()
        self.ai_id = "ai_agent_0"
        self.render_mode = render_mode

        # Actions: 0: None, 1: Fwd, 2: Back, 3: Turn Left, 4: Turn Right, 5: Shoot
        self.action_space = spaces.Discrete(6)

        # Observation: Local grid centered on tank (e.g., 15x15)
        self.obs_size = 15
        self.half_obs = self.obs_size // 2
        # Values: 0=Empty, 1=Wall, 2=Fog, 3=Self, 4=Enemy, 5=Bullet
        self.observation_space = spaces.Box(low=0, high=5, shape=(self.obs_size, self.obs_size), dtype=np.uint8)

        self.max_steps = 1000
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game = TankGame() # Reset map and everything
        self.game.add_tank(self.ai_id)

        # Add a dummy enemy for training
        self.enemy_id = "enemy_1"
        self.game.add_tank(self.enemy_id)

        self.current_step = 0
        observation = self._get_obs()
        info = {}
        return observation, info

    def step(self, action):
        fwd, turn = 0, 0
        if action == 1: fwd = 1
        elif action == 2: fwd = -1
        elif action == 3: turn = -1
        elif action == 4: turn = 1
        elif action == 5: self.game.shoot_bullet(self.ai_id)

        if fwd != 0 or turn != 0:
            self.game.move_tank(self.ai_id, forward=fwd, turn=turn)

        # Dummy enemy logic (random movement occasionally)
        if np.random.rand() < 0.2:
            self.game.move_tank(self.enemy_id, forward=np.random.choice([-1, 0, 1]), turn=np.random.choice([-1, 0, 1]))
        if np.random.rand() < 0.05:
            self.game.shoot_bullet(self.enemy_id)

        self.game.update()

        self.current_step += 1
        obs = self._get_obs()

        reward = 0.0
        terminated = False
        truncated = False

        # Reward shaping
        ai_tank = self.game.tanks.get(self.ai_id)
        enemy_tank = self.game.tanks.get(self.enemy_id)

        if not ai_tank or not ai_tank.active:
            reward = -10.0
            terminated = True
        elif not enemy_tank or not enemy_tank.active:
            reward = 10.0
            terminated = True
        else:
            # Small penalty for time to encourage action
            reward = -0.01
            # Reward for hitting enemy could be tracked via health changes
            if enemy_tank.health < 3:
                reward += 1.0 # simplistic reward for dealing damage

        if self.current_step >= self.max_steps:
            truncated = True

        return obs, reward, terminated, truncated, {}

    def _get_obs(self):
        obs = np.full((self.obs_size, self.obs_size), 2, dtype=np.uint8) # Default is fog (2)

        if self.ai_id not in self.game.tanks:
            return obs

        tank = self.game.tanks[self.ai_id]
        if not tank.active:
            return obs

        state = self.game.get_state(pov_tank_id=self.ai_id)
        grid = state['grid']

        tx, ty = int(tank.x), int(tank.y)

        for oy in range(self.obs_size):
            for ox in range(self.obs_size):
                gx = tx - self.half_obs + ox
                gy = ty - self.half_obs + oy

                if 0 <= gx < self.game.width and 0 <= gy < self.game.height:
                    obs[oy, ox] = grid[gy][gx]
                else:
                    obs[oy, ox] = 1 # Bounds are walls

        # Overlay self
        obs[self.half_obs, self.half_obs] = 3

        # Overlay enemies and bullets (relative positions)
        for tid, t in state['tanks'].items():
            if tid != self.ai_id and t['visible']:
                rel_x = int(t['x']) - tx + self.half_obs
                rel_y = int(t['y']) - ty + self.half_obs
                if 0 <= rel_x < self.obs_size and 0 <= rel_y < self.obs_size:
                    obs[rel_y, rel_x] = 4

        for b in state['bullets']:
            rel_x = int(b['x']) - tx + self.half_obs
            rel_y = int(b['y']) - ty + self.half_obs
            if 0 <= rel_x < self.obs_size and 0 <= rel_y < self.obs_size:
                obs[rel_y, rel_x] = 5

        return obs

    def render(self):
        pass # Implemented in frontend via WebSocket normally, but can add CLI debug
