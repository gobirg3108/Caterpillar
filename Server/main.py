import asyncio
import json
import logging
import threading
import os
import sys

import pyautogui
import time

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymodbus.client import ModbusTcpClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CNC Modbus API", version="1.0.0")

# ── Middleware FIRST (before any routes or mounts) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 502
TOTAL_COILS = 13
FEED_RATE_REGISTER = 0

connected_clients: list[WebSocket] = []

# ════════════════════════════════════════
#  Auto Click Config
# ════════════════════════════════════════

BUTTONS = [
    ( 1095,  450,  "MEMORY",          5 ),
    ( 1230,  450,  "EDIT",            5 ),
    ( 1370,  450,  "MDI",             5 ),
    ( 1510,  450,  "OPTIONAL STOP",   5 ),
    ( 1645,  450,  "SINGLE BLOCK",    5 ),
    ( 1785,  450,  "FEED HOLD",       5 ),
    ( 1250,  650,  "TABLE STOP",      5 ),
    ( 1333,  650,  "CYCLE START",     5 ),
    ( 1414,  650,  "COOLANT ON",      5 ),
    ( 1500,  650,  "BLOCK SKIP",      5 ),
    ( 1580,  650,  "RESET",           5 ),
    ( 1660,  650,  "DOOR I/L",        5 ),
    ( 1790,  645,  "E-STOP",          5 ),
    ( 1555,  810,  "RESET ALL",       5 ),
    ( 1095,  450,  "MEMORY",          5 ),
    ( 1510,  450,  "OPTIONAL STOP",   5 ),
    ( 1645,  450,  "SINGLE BLOCK",    5 ),
    ( 1414,  650,  "COOLANT ON",      5 ),
    ( 1555,  810,  "RESET ALL",       5 ),
    ( 1355,  810,  "AUTTO OFF",       5 ),
]

MOVE_DURATION = 0.4
pyautogui.FAILSAFE = True

auto_mode_active = False
auto_thread: threading.Thread | None = None
auto_stop_event = threading.Event()


def run_auto_click():
    logger.info("Auto click sequence started")
    for i, (x, y, name, delay) in enumerate(BUTTONS, 1):
        if auto_stop_event.is_set():
            logger.info("Auto click stopped by user")
            break
        logger.info(f"[{i:02d}/{len(BUTTONS)}] Clicking {name} at ({x}, {y})")
        try:
            pyautogui.moveTo(x, y, duration=MOVE_DURATION)
            pyautogui.click()
        except Exception as e:
            logger.error(f"Auto click error at {name}: {e}")
        for _ in range(delay * 10):
            if auto_stop_event.is_set():
                break
            time.sleep(0.1)
    logger.info("Auto click sequence finished")


# ════════════════════════════════════════
#  Modbus helpers
# ════════════════════════════════════════

def get_client():
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    connected = client.connect()
    return client, connected

def read_all_coils() -> dict:
    client, connected = get_client()
    if not connected:
        client.close()
        return {}
    try:
        result = client.read_coils(address=0, count=TOTAL_COILS)
        if hasattr(result, "isError") and result.isError():
            return {}
        if isinstance(result, Exception):
            return {}
        bits = result.bits if hasattr(result, "bits") else []
        return {i: bool(bit) for i, bit in enumerate(bits[:TOTAL_COILS])}
    except Exception as e:
        logger.error(f"read_all_coils: {e}")
        return {}
    finally:
        client.close()

def read_feed_rate() -> int:
    client, connected = get_client()
    if not connected:
        client.close()
        return 0
    try:
        result = client.read_holding_registers(address=FEED_RATE_REGISTER, count=1)
        if isinstance(result, Exception):
            return 0
        if hasattr(result, "isError") and result.isError():
            return 0
        regs = result.registers if hasattr(result, "registers") else [0]
        return regs[0]
    except Exception as e:
        logger.error(f"read_feed_rate: {e}")
        return 0
    finally:
        client.close()

def toggle_coil(coil: int) -> dict:
    client, connected = get_client()
    if not connected:
        client.close()
        raise HTTPException(status_code=503, detail="Modbus connection failed")
    try:
        read_result = client.read_coils(address=coil, count=1)
        if isinstance(read_result, Exception):
            raise HTTPException(status_code=500, detail=str(read_result))
        if hasattr(read_result, "isError") and read_result.isError():
            raise HTTPException(status_code=500, detail="Failed to read coil")
        bits = read_result.bits if hasattr(read_result, "bits") else [False]
        new_state = not bool(bits[0])
        client.write_coil(address=coil, value=new_state)
        logger.info(f"Coil {coil} -> {new_state}")
        return {"coil": coil, "state": new_state}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"toggle_coil: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

def write_feed_rate(value: int) -> dict:
    client, connected = get_client()
    if not connected:
        client.close()
        raise HTTPException(status_code=503, detail="Modbus connection failed")
    try:
        client.write_register(address=FEED_RATE_REGISTER, value=value)
        logger.info(f"Feed Rate -> {value}")
        return {"register": FEED_RATE_REGISTER, "value": value}
    except Exception as e:
        logger.error(f"write_feed_rate: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()

def reset_all_coils() -> dict:
    client, connected = get_client()
    if not connected:
        client.close()
        raise HTTPException(status_code=503, detail="Modbus connection failed")
    try:
        for i in range(TOTAL_COILS):
            client.write_coil(address=i, value=False)
        client.write_register(address=FEED_RATE_REGISTER, value=0)
        logger.info("All coils reset to 0, Feed Rate reset to 0")
        return {"reset": True, "coils_cleared": TOTAL_COILS, "feed_rate": 0}
    except Exception as e:
        logger.error(f"reset_all_coils: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        client.close()


# ════════════════════════════════════════
#  WebSocket
# ════════════════════════════════════════

async def broadcast(data: dict):
    message = json.dumps(data)
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)

async def modbus_watcher():
    previous = {}
    while True:
        await asyncio.sleep(0.5)
        if not connected_clients:
            continue
        loop = asyncio.get_event_loop()
        coils = await loop.run_in_executor(None, read_all_coils)
        feed  = await loop.run_in_executor(None, read_feed_rate)
        current = {"coil_states": coils, "feed_rate": feed}
        if current != previous:
            await broadcast(current)
            previous = current

@app.on_event("startup")
async def startup():
    asyncio.create_task(modbus_watcher())
    logger.info("Modbus watcher started ✅")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    loop = asyncio.get_event_loop()
    coils = await loop.run_in_executor(None, read_all_coils)
    feed  = await loop.run_in_executor(None, read_feed_rate)
    await websocket.send_text(json.dumps({"coil_states": coils, "feed_rate": feed}))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


# ════════════════════════════════════════
#  REST endpoints
# ════════════════════════════════════════

def make_endpoint(command: str, coil: int, message: str):
    @app.post(f"/{command}", summary=message)
    async def handler():
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, toggle_coil, coil)
        coils = await loop.run_in_executor(None, read_all_coils)
        feed  = await loop.run_in_executor(None, read_feed_rate)
        await broadcast({"coil_states": coils, "feed_rate": feed})
        return {"success": True, "message": message, "modbus": result}
    handler.__name__ = command.replace("-", "_")
    return handler

make_endpoint("memory",         0,  "Memory Mode")
make_endpoint("edit",           1,  "Edit Mode")
make_endpoint("mdi",            2,  "MDI Mode")
make_endpoint("optional-stop",  3,  "Optional Stop")
make_endpoint("single-block",   4,  "Single Block")
make_endpoint("feed-hold",      5,  "Feed Hold")
make_endpoint("table-stop",     6,  "Table Stop")
make_endpoint("cycle-start",    7,  "Cycle Start")
make_endpoint("coolant",        8,  "Coolant")
make_endpoint("block-skip",     9,  "Block Skip")
make_endpoint("reset",          10, "Reset")
make_endpoint("door-interlock", 11, "Door Interlock")
make_endpoint("emergency",      12, "Emergency")

class FeedRateRequest(BaseModel):
    value: int

@app.post("/feed-rate", summary="Feed Rate")
async def feed_rate(body: FeedRateRequest):
    if not (0 <= body.value <= 120):
        raise HTTPException(status_code=400, detail="Value must be between 0 and 120")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, write_feed_rate, body.value)
    coils = await loop.run_in_executor(None, read_all_coils)
    feed  = await loop.run_in_executor(None, read_feed_rate)
    await broadcast({"coil_states": coils, "feed_rate": feed})
    return {"success": True, "message": "Feed Rate updated", "modbus": result}

@app.post("/reset-all", summary="Reset All Coils and Feed Rate")
async def reset_all():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, reset_all_coils)
    coils = await loop.run_in_executor(None, read_all_coils)
    feed  = await loop.run_in_executor(None, read_feed_rate)
    await broadcast({"coil_states": coils, "feed_rate": feed})
    return {"success": True, "message": "All coils reset to OFF", "modbus": result}

@app.post("/auto-click/start")
async def start_auto_click():
    global auto_mode_active, auto_thread, auto_stop_event
    if auto_mode_active and auto_thread and auto_thread.is_alive():
        return {"success": False, "message": "Auto click already running"}
    auto_stop_event.clear()
    auto_mode_active = True
    auto_thread = threading.Thread(target=run_auto_click, daemon=True)
    auto_thread.start()
    return {"success": True, "message": "Auto click started"}

@app.post("/auto-click/stop")
async def stop_auto_click():
    global auto_mode_active
    auto_stop_event.set()
    auto_mode_active = False
    return {"success": True, "message": "Auto click stopped"}

@app.get("/auto-click/status")
async def auto_click_status():
    running = auto_mode_active and auto_thread is not None and auto_thread.is_alive()
    return {"auto_mode": running}

@app.get("/health")
async def health():
    return {"status": "ok", "server": "CNC Modbus API"}

@app.get("/status")
async def modbus_status():
    loop = asyncio.get_event_loop()
    coils = await loop.run_in_executor(None, read_all_coils)
    feed  = await loop.run_in_executor(None, read_feed_rate)
    return {
        "modbus_connected": len(coils) > 0,
        "host": MODBUS_HOST,
        "port": MODBUS_PORT,
        "coil_states": coils,
        "feed_rate": feed,
    }

# ── Serve React frontend — MUST be LAST, after all API routes ──
def get_dist_dir():
    # Works both in dev and inside PyInstaller .exe
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, "dist")

dist_dir = get_dist_dir()
if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")
    logger.info(f"Serving frontend from: {dist_dir}")
else:
    logger.warning(f"No dist/ folder found at: {dist_dir}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)