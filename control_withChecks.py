import asyncio
import logging
from mavsdk import System

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

async def connect_drone(serial_port="/dev/ttyACM0", baudrate=57600) -> System:
    drone = System()
    await drone.connect(system_address=f"serial://{serial_port}:{baudrate}")
    logging.info("🔌 Connecting to drone...")

    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("✅ Drone connected successfully.")
            break
    return drone

async def check_basic_health(drone: System):
    logging.info("🩺 Checking basic health (gyro, accel)...")
    async for health in drone.telemetry.health():
        if health.is_gyrometer_calibration_ok and health.is_accelerometer_calibration_ok:
            logging.info("✅ Gyroscope and accelerometer OK.")
            break
        else:
            logging.warning("⚠️ Waiting for gyro/accel calibration...")
            await asyncio.sleep(1)

async def check_gps_health(drone: System):
    logging.info("📡 Checking GPS lock status...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logging.info("✅ GPS lock acquired. Home position OK.")
            break
        else:
            logging.warning("⏳ Waiting for GPS lock...")
            await asyncio.sleep(1)

async def check_rc_signal(drone: System):
    logging.info("🎮 Checking RC signal via RcStatus...")

    async for rc_status in drone.telemetry.rc_status():
        if rc_status.is_available:
            logging.info(f"✅ RC signal detected. Strength: {rc_status.signal_strength_percent:.1f}%")
            break
        elif rc_status.was_available_once:
            logging.warning("⚠️ RC was available earlier but is not now.")
        else:
            logging.warning("⏳ No RC signal detected yet.")
        await asyncio.sleep(1)


async def check_armable(drone: System):
    logging.info("✅ Checking if drone is armable...")
    async for is_armed in drone.telemetry.armed():
        if not is_armed:
            logging.info("🛑 Drone is currently disarmed and ready to be armed.")
            break
        else:
            logging.warning("⚠️ Drone already armed?")
            await asyncio.sleep(1)

async def arm_drone(drone: System):
    logging.info("🚀 Sending arm command...")
    try:
        await drone.action.arm()
        logging.info("✅ Drone successfully armed!")
    except Exception as e:
        logging.error(f"❌ Failed to arm drone: {e}")

async def main():
    drone = await connect_drone()
    await check_basic_health(drone)
    await check_gps_health(drone)
    await check_rc_signal(drone)  
    await check_armable(drone)
    await arm_drone(drone)

if __name__ == "__main__":
    asyncio.run(main())
