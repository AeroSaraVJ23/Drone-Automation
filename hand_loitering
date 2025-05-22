import asyncio
from mavsdk import System
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

async def connect_drone():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")
    logging.info("🔌 Connecting to drone...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("✅ Drone connected.")
            break
    return drone

async def wait_for_position(drone):
    logging.info("📡 Waiting for GPS and altitude data...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logging.info("✅ GPS and home position OK.")
            break
        await asyncio.sleep(1)

async def read_altitude(drone):
    logging.info("📈 Reading altitude. Lift the drone by hand now...")

    async for pos in drone.telemetry.position():
        logging.info(f"Altitude above ground (relative): {pos.relative_altitude_m:.2f} m")
        await asyncio.sleep(1)  # Read every 1 second

async def main():
    drone = await connect_drone()
    await wait_for_position(drone)
    await read_altitude(drone)

if __name__ == "__main__":
    asyncio.run(main())
