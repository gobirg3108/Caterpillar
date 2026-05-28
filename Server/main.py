import asyncio
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
        result = client.write_coil(coil, new_state)

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


make_endpoint("cycle-start",   0, "Cycle Start")
make_endpoint("feed-hold",     1, "Feed Hold")
make_endpoint("reset",         2, "Reset")
make_endpoint("coolant",       3, "Coolant")
make_endpoint("emergency",     4, "Emergency")
make_endpoint("optional-stop", 5, "Optional Stop")
make_endpoint("single-block",  6, "Single Block")
make_endpoint("block-skip",    7, "Block Skip")


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
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )