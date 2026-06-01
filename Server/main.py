import asyncio
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymodbus.client import ModbusTcpClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CNC Modbus API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 502

# Store current coil states
coil_states = {}

# Feed rate register address
FEED_RATE_REGISTER = 0


def toggle_coil(coil: int) -> dict:
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

    connected = client.connect()
    logger.info(f"Modbus connected: {connected}")

    if not connected:
        raise HTTPException(status_code=503, detail="Modbus connection failed")

    try:
        # Current state
        current_state = coil_states.get(coil, False)

        # Toggle state
        new_state = not current_state

        # Write to PLC
        result = client.read_coils().write_coil(coil, new_state)

        # Save new state
        coil_states[coil] = new_state

        logger.info(f"Coil {coil} -> {new_state}")

        return {
            "coil": coil,
            "state": new_state,
            "result": str(result)
        }

    finally:
        client.close()


def write_feed_rate(value: int) -> dict:
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

    connected = client.connect()
    logger.info(f"Modbus connected: {connected}")

    if not connected:
        raise HTTPException(status_code=503, detail="Modbus connection failed")

    try:
        # value range: 0 to 120, direct write
        result = client.write_register(FEED_RATE_REGISTER, value)

        logger.info(f"Feed Rate register {FEED_RATE_REGISTER} -> {value}")

        return {
            "register": FEED_RATE_REGISTER,
            "value": value,
            "result": str(result)
        }

    finally:
        client.close()


def make_endpoint(command: str, coil: int, message: str):

    @app.post(f"/{command}", summary=message)
    async def handler():

        logger.info(f"Command: {command} (coil {coil})")

        loop = asyncio.get_event_loop()

        result = await loop.run_in_executor(
            None,
            toggle_coil,
            coil
        )

        return {
            "success": True,
            "message": message,
            "modbus": result
        }

    handler.__name__ = command.replace("-", "_")

    return handler


make_endpoint("cycle-start",    0, "Cycle Start")
make_endpoint("feed-hold",      1, "Feed Hold")
make_endpoint("reset",          2, "Reset")
make_endpoint("coolant",        3, "Coolant")
make_endpoint("emergency",      4, "Emergency")
make_endpoint("optional-stop",  5, "Optional Stop")
make_endpoint("single-block",   6, "Single Block")
make_endpoint("block-skip",     7, "Block Skip")
make_endpoint("memory",         8, "Memory Mode")
make_endpoint("edit",           9, "Edit Mode")
make_endpoint("mdi",           10, "MDI Mode")
make_endpoint("table-stop",    11, "Table Stop")
make_endpoint("door-interlock",12, "Door Interlock")


class FeedRateRequest(BaseModel):
    value: int  # 0 to 120


@app.post("/feed-rate", summary="Feed Rate")
async def feed_rate(body: FeedRateRequest):
    if not (0 <= body.value <= 120):
        raise HTTPException(status_code=400, detail="Value must be between 0 and 120")

    logger.info(f"Feed Rate: {body.value}")

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, write_feed_rate, body.value)

    return {
        "success": True,
        "message": "Feed Rate updated",
        "modbus": result
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "server": "CNC Modbus API"
    }


@app.get("/status")
async def modbus_status():

    client = ModbusTcpClient(
        MODBUS_HOST,
        port=MODBUS_PORT
    )

    connected = client.connect()

    client.close()

    return {
        "modbus_connected": connected,
        "host": MODBUS_HOST,
        "port": MODBUS_PORT,
        "coil_states": coil_states
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
    )
