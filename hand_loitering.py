import asyncio
import logging
from mavsdk import System

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

async def print_altitude_info(drone):
    # Get Home Position
    logging.info("📍 Waiting for home position to be set...")
    home = None
    async for hp in drone.telemetry.home():
        home = hp
        logging.info("✅ Home position received.")
        break

    # Print current altitude data in tab-separated format
    print("Home Altitude (m)\tCurrent Altitude (m)\tRelative Altitude (m)")
    async for pos in drone.telemetry.position():
        print(f"{home.absolute_altitude_m:.2f}\t\t\t{pos.absolute_altitude_m:.2f}\t\t\t{pos.relative_altitude_m:.2f}")
        await asyncio.sleep(1)

async def main():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    logging.info("🔌 Connecting to drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("✅ Drone connected.")
            break

    await print_altitude_info(drone)

if __name__ == "__main__":
    asyncio.run(main())
