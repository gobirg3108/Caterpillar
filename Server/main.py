from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymodbus.client import ModbusTcpClient
import asyncio
import logging

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
PULSE_DURATION = 1.0  # seconds

COIL_MAP = {
    "cycle-start": 0,
    "feed-hold": 1,
    "reset": 2,
    "coolant": 3,
    "emergency": 4,
    "optional-stop": 5,
    "single-block": 6,
    "block-skip": 7,
}


def pulse_coil(coil: int) -> dict:
    """Connect to Modbus, pulse a coil ON then OFF after PULSE_DURATION seconds."""
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    connected = client.connect()
    logger.info(f"Modbus connected: {connected}")

    if not connected:
        raise HTTPException(status_code=503, detail="Modbus connection failed")

    try:
        result_on = client.write_coil(coil, True)
        logger.info(f"Coil {coil} ON: {result_on}")

        import time
        time.sleep(PULSE_DURATION)

        result_off = client.write_coil(coil, False)
        logger.info(f"Coil {coil} OFF: {result_off}")

        return {"coil": coil, "on_result": str(result_on), "off_result": str(result_off)}
    finally:
        client.close()


def make_endpoint(command: str, coil: int, message: str):
    """Factory to create POST endpoints for each CNC command."""
    @app.post(f"/{command}", summary=message)
    async def handler():
        logger.info(f"Command: {command} (coil {coil})")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, pulse_coil, coil)
        return {"success": True, "message": message, "modbus": result}
    handler.__name__ = command.replace("-", "_")
    return handler


make_endpoint("cycle-start",   0, "Cycle Start Sent")
make_endpoint("feed-hold",     1, "Feed Hold Sent")
make_endpoint("reset",         2, "Reset Sent")
make_endpoint("coolant",       3, "Coolant Sent")
make_endpoint("emergency",     4, "Emergency Triggered")
make_endpoint("optional-stop", 5, "Optional Stop Sent")
make_endpoint("single-block",  6, "Single Block Sent")
make_endpoint("block-skip",    7, "Block Skip Sent")


@app.get("/health")
async def health():
    return {"status": "ok", "server": "CNC Modbus API"}


@app.get("/status")
async def modbus_status():
    """Check Modbus TCP connection status."""
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    connected = client.connect()
    client.close()
    return {"modbus_connected": connected, "host": MODBUS_HOST, "port": MODBUS_PORT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
