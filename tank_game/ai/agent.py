import numpy as np
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from env import TankEnv

try:
    from stable_baselines3 import PPO
    HAS_SB3 = True
except ImportError:
    HAS_SB3 = False

class DummyAgent:
    def __init__(self, ai_id: str, model_path: str = None):
        self.ai_id = ai_id
        self.model = None
        self.obs_size = 15
        self.half_obs = self.obs_size // 2

        if model_path and os.path.exists(model_path) and HAS_SB3:
            print(f"Loading trained AI model for {ai_id}")
            self.model = PPO.load(model_path)
        else:
            print(f"Using random fallback AI for {ai_id}")

    def _extract_obs(self, state: dict) -> np.ndarray:
        obs = np.full((self.obs_size, self.obs_size), 2, dtype=np.uint8) # Default fog

        tanks = state.get('tanks', {})
        if self.ai_id not in tanks:
            return obs

        tank = tanks[self.ai_id]
        if not tank.get('active', True):
            return obs

        grid = state.get('grid', [])
        width = state.get('width', 40)
        height = state.get('height', 40)

        tx, ty = int(tank['x']), int(tank['y'])

        # Build local grid
        for oy in range(self.obs_size):
            for ox in range(self.obs_size):
                gx = tx - self.half_obs + ox
                gy = ty - self.half_obs + oy

                if 0 <= gx < width and 0 <= gy < height:
                    try:
                        obs[oy, ox] = grid[gy][gx]
                    except IndexError:
                        pass
                else:
                    obs[oy, ox] = 1 # Wall

        obs[self.half_obs, self.half_obs] = 3 # Self

        # Enemies
        for tid, t in tanks.items():
            if tid != self.ai_id and t.get('visible', False):
                rel_x = int(t['x']) - tx + self.half_obs
                rel_y = int(t['y']) - ty + self.half_obs
                if 0 <= rel_x < self.obs_size and 0 <= rel_y < self.obs_size:
                    obs[rel_y, rel_x] = 4

        # Bullets
        for b in state.get('bullets', []):
            rel_x = int(b['x']) - tx + self.half_obs
            rel_y = int(b['y']) - ty + self.half_obs
            if 0 <= rel_x < self.obs_size and 0 <= rel_y < self.obs_size:
                obs[rel_y, rel_x] = 5

        return obs

    def predict(self, state: dict) -> int:
        """Returns action: 0: None, 1: Fwd, 2: Back, 3: Turn Left, 4: Turn Right, 5: Shoot"""

        if self.model:
            obs = self._extract_obs(state)
            action, _ = self.model.predict(obs, deterministic=True)
            return int(action)
        else:
            # Fallback random logic
            rnd = np.random.random()
            if rnd < 0.1: return 1 # Fwd
            elif rnd < 0.2: return 2 # Back
            elif rnd < 0.3: return 3 # Turn L
            elif rnd < 0.4: return 4 # Turn R
            elif rnd < 0.45: return 5 # Shoot
            return 0 # Do nothing
