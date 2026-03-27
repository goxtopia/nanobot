# Tank Battle Game

A web-based multiplayer tank battle game featuring real-time WebSocket communication, random map generation, fog of war, and Reinforcement Learning (RL) AI agents.

## Features

- **Multiplayer**: Connect via WebSockets. Multiple humans can play in the same room.
- **Fog of War**: You can only see enemies and bullets within your tank's line of sight.
- **Random Maps**: Procedurally generated maps with variations (Empty, Obstacles, Dense/Maze).
- **AI Opponents**: Add AI opponents on the fly. You can train them using DQN/PPO.
- **Terrain Occlusion**: Bullets bounce off walls, and vision is blocked by terrain.

## Installation

1. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game Server

To start the backend FastAPI server and serve the frontend:

```bash
cd tank_game
python backend/main.py
```

The game will be accessible at `http://localhost:8000`.
- **Controls**: Use `Arrow Keys` or `WASD` to move. Press `Space` to shoot.
- **Add AI**: Click the "Add AI Opponent" button on the UI to spawn an AI in the game.

## Training the AI (Reinforcement Learning)

The game uses `stable-baselines3` to train agents via a custom Gymnasium environment.

To start training a PPO agent:

```bash
cd tank_game/ai
python train.py
```

- **Checkpoints**: The script automatically saves checkpoints in `tank_game/ai/logs/` during training.
- **Final Model**: The final trained model will be saved as `models/ppo_tank_final.zip`.

*Note: You can load the trained model by passing the path to the `DummyAgent` constructor in `backend/main.py`.*

## Running Tests

We use `pytest` for unit testing the core game mechanics (movement, collisions, fog of war).

From the root of the project:

```bash
PYTHONPATH=tank_game python -m pytest tank_game/tests/
```
