import asyncio
import logging
from mavsdk import System
from mavsdk.telemetry import Health

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

async def connect_drone(serial_port="/dev/ttyACM0", baudrate=57600) -> System:
    drone = System()
    await drone.connect(system_address=f"serial://{serial_port}:{baudrate}")
    logging.info("Connecting to drone...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("✅ Drone connected.")
            break
    return drone

async def check_health(drone: System):
    logging.info("Checking basic health status (ignoring GPS/RC)...")
    async for health in drone.telemetry.health():
        # We skip GPS and RC checks
        if health.is_gyrometer_calibration_ok and health.is_accelerometer_calibration_ok:
            logging.info("✅ Gyro and Accelerometer OK.")
            break
        else:
            logging.warning("⚠️ Waiting for sensor calibration...")
            await asyncio.sleep(1)

async def check_armable(drone: System):
    logging.info("Waiting until drone is armable...")
    async for is_armable in drone.telemetry.armed():
        if not is_armable:
            logging.info("Drone is currently disarmed and ready for arming.")
            break
        else:
            logging.warning("⚠️ Drone already armed?")
            await asyncio.sleep(1)

async def arm_drone(drone: System):
    logging.info("Sending arm command...")
    try:
        await drone.action.arm()
        logging.info("✅ Drone armed.")
    except Exception as e:
        logging.error(f"❌ Failed to arm drone: {e}")

async def main():
    drone = await connect_drone()
    await check_health(drone)
    await check_armable(drone)
    await arm_drone(drone)

if __name__ == "__main__":
    asyncio.run(main())
