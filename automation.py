import asyncio
import logging
from mavsdk import System

# Configure logging
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

async def arm_and_takeoff(drone, target_altitude=2.0):
    logging.info("🚀 Arming drone...")
    await drone.action.arm()

    logging.info(f"⬆️ Taking off to {target_altitude} meters...")
    await drone.action.takeoff()
    await asyncio.sleep(10)  # Allow time to reach altitude

    async for pos in drone.telemetry.position():
        logging.info(f"📍 Current altitude: {pos.relative_altitude_m:.2f} m")
        if pos.relative_altitude_m >= target_altitude - 0.2:
            logging.info("✅ Target altitude reached.")
            break
        await asyncio.sleep(1)

async def hold_position(drone, hold_duration=10):
    logging.info(f"⏸ Holding position for {hold_duration} seconds...")
    await asyncio.sleep(hold_duration)
    logging.info("✅ Hold complete.")

async def land_drone(drone):
    logging.info("🛬 Initiating landing...")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            logging.info("✅ Drone has landed.")
            break
        await asyncio.sleep(1)

async def main():
    drone = await connect_drone()
    await arm_and_takeoff(drone, target_altitude=2.0)  # Set altitude in meters
    await hold_position(drone, hold_duration=10)       # Hold for 10 seconds
    await land_drone(drone)

if __name__ == "__main__":
    asyncio.run(main())
