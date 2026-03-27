import asyncio
import json
import logging
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import sys

# Ensure backend imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.game import TankGame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tank_server")

app = FastAPI()

# Mount frontend files
app.mount("/static", StaticFiles(directory="tank_game/frontend"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("tank_game/frontend/index.html")

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()
game = TankGame()
game_task = None
fps = 30
tick_time = 1.0 / fps

# AI loop integration placeholder
ai_agents = {}

async def game_loop():
    logger.info("Game loop started.")
    while True:
        try:
            # Integrate AI actions if any
            for ai_id, agent in ai_agents.items():
                if ai_id in game.tanks and game.tanks[ai_id].active:
                    state = game.get_state(pov_tank_id=ai_id)
                    action = agent.predict(state) # 0: None, 1: Fwd, 2: Back, 3: Left, 4: Right, 5: Shoot
                    fwd, turn = 0, 0
                    if action == 1: fwd = 1
                    elif action == 2: fwd = -1
                    elif action == 3: turn = -1
                    elif action == 4: turn = 1
                    elif action == 5: game.shoot_bullet(ai_id)

                    if fwd != 0 or turn != 0:
                        game.move_tank(ai_id, forward=fwd, turn=turn)

            game.update()

            # Broadcast state to each client based on their POV (Fog of War)
            for client_id in manager.active_connections.keys():
                state = game.get_state(pov_tank_id=client_id)
                await manager.send_personal_message(json.dumps({"type": "state", "data": state}), client_id)

            await asyncio.sleep(tick_time)
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            await asyncio.sleep(tick_time)

@app.on_event("startup")
async def startup_event():
    global game_task
    game_task = asyncio.create_task(game_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    game.add_tank(client_id)

    # Send initial info
    await manager.send_personal_message(json.dumps({
        "type": "init",
        "client_id": client_id,
        "width": game.width,
        "height": game.height
    }), client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "input":
                inputs = message["data"]
                fwd = 0
                turn = 0
                if inputs.get("up"): fwd = 1
                elif inputs.get("down"): fwd = -1

                if inputs.get("left"): turn = -1
                elif inputs.get("right"): turn = 1

                game.move_tank(client_id, forward=fwd, turn=turn)

                if inputs.get("shoot"):
                    game.shoot_bullet(client_id)

            elif message["type"] == "spawn_ai":
                # For demonstration, handle dynamic AI spawning
                ai_id = f"ai_{uuid.uuid4().hex[:8]}"
                game.add_tank(ai_id)
                # We'll need to inject a basic agent here later,
                # for now, placeholder random agent
                from ai.agent import DummyAgent # Will be implemented
                ai_agents[ai_id] = DummyAgent(ai_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        game.remove_tank(client_id)
        logger.info(f"Client {client_id} disconnected.")
    except Exception as e:
        logger.error(f"Websocket error: {e}")
        manager.disconnect(client_id)
        game.remove_tank(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
