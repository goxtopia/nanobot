const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const statusDiv = document.getElementById("status");
const hpDiv = document.getElementById("hp");
const addAiBtn = document.getElementById("add-ai-btn");

let socket;
let clientId = null;
let gameState = null;

// Display settings
const CELL_SIZE = 20; // Pixels per grid unit
let canvasWidth = 800;
let canvasHeight = 800;

// Inputs
const keys = {
    up: false,
    down: false,
    left: false,
    right: false,
    shoot: false
};

function connect() {
    socket = new WebSocket(`ws://${window.location.host}/ws`);

    socket.onopen = () => {
        statusDiv.innerText = "Connected";
        statusDiv.style.color = "#00ff00";
    };

    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "init") {
            clientId = msg.client_id;
            canvasWidth = msg.width * CELL_SIZE;
            canvasHeight = msg.height * CELL_SIZE;
            canvas.width = canvasWidth;
            canvas.height = canvasHeight;
        } else if (msg.type === "state") {
            gameState = msg.data;
            updateUI();
            draw();
        }
    };

    socket.onclose = () => {
        statusDiv.innerText = "Disconnected";
        statusDiv.style.color = "#ff0000";
        setTimeout(connect, 3000); // Reconnect attempt
    };

    socket.onerror = (err) => {
        console.error("Socket error", err);
    };
}

function updateUI() {
    if (!gameState || !clientId) return;
    const myTank = gameState.tanks[clientId];
    if (myTank) {
        hpDiv.innerText = `HP: ${myTank.hp}`;
    } else {
        hpDiv.innerText = "DEAD / SPECTATING";
    }
}

function sendInput() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "input",
            data: keys
        }));
        // Reset shoot so it's a pulse, not continuous stream if held
        if (keys.shoot) keys.shoot = false;
    }
}

// Input Handlers
window.addEventListener("keydown", (e) => {
    switch(e.code) {
        case "ArrowUp": case "KeyW": keys.up = true; break;
        case "ArrowDown": case "KeyS": keys.down = true; break;
        case "ArrowLeft": case "KeyA": keys.left = true; break;
        case "ArrowRight": case "KeyD": keys.right = true; break;
        case "Space": keys.shoot = true; break;
    }
});

window.addEventListener("keyup", (e) => {
    switch(e.code) {
        case "ArrowUp": case "KeyW": keys.up = false; break;
        case "ArrowDown": case "KeyS": keys.down = false; break;
        case "ArrowLeft": case "KeyA": keys.left = false; break;
        case "ArrowRight": case "KeyD": keys.right = false; break;
        case "Space": keys.shoot = false; break;
    }
});

addAiBtn.addEventListener("click", () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({type: "spawn_ai"}));
    }
});

function drawTank(t, isMe) {
    ctx.save();
    ctx.translate(t.x * CELL_SIZE, t.y * CELL_SIZE);

    // Rotation based on dir_x and dir_y
    const angle = Math.atan2(t.dir_y, t.dir_x);
    ctx.rotate(angle);

    // Draw body
    ctx.fillStyle = isMe ? "#4caf50" : "#f44336"; // Green for self, Red for enemies
    ctx.fillRect(-8, -8, 16, 16);

    // Draw barrel
    ctx.fillStyle = "#888";
    ctx.fillRect(0, -2, 12, 4);

    ctx.restore();

    // Health bar
    ctx.fillStyle = "red";
    ctx.fillRect(t.x * CELL_SIZE - 10, t.y * CELL_SIZE - 15, 20, 3);
    ctx.fillStyle = "green";
    ctx.fillRect(t.x * CELL_SIZE - 10, t.y * CELL_SIZE - 15, 20 * (t.hp / 3), 3);
}

function draw() {
    if (!gameState) return;

    // Clear background
    ctx.fillStyle = "#111";
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    // Draw Grid / Map
    const grid = gameState.grid;
    for (let y = 0; y < gameState.height; y++) {
        for (let x = 0; x < gameState.width; x++) {
            const val = grid[y][x];
            if (val === 1) {
                // Wall
                ctx.fillStyle = "#555";
                ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            } else if (val === 2) {
                // Fog
                ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
                ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            } else {
                // Floor
                ctx.fillStyle = "#222";
                ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            }
        }
    }

    // Draw Bullets
    ctx.fillStyle = "#ffeb3b";
    for (const b of gameState.bullets) {
        ctx.beginPath();
        ctx.arc(b.x * CELL_SIZE, b.y * CELL_SIZE, 3, 0, Math.PI * 2);
        ctx.fill();
    }

    // Draw Tanks
    for (const tid in gameState.tanks) {
        const t = gameState.tanks[tid];
        if (t.visible) {
            drawTank(t, tid === clientId);
        }
    }
}

// Loop for inputs
setInterval(sendInput, 1000/60); // 60hz input sending

connect();
