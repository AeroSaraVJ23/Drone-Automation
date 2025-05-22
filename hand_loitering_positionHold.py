import asyncio
import logging
from mavsdk import System

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

async def get_stable_altitude(drone, stability_duration=3):
    logging.info("📈 Waiting for a stable altitude...")

    stable_altitudes = []

    for _ in range(stability_duration):
        async for pos in drone.telemetry.position():
            stable_altitudes.append(pos.relative_altitude_m)
            logging.info(f"Reading: {pos.relative_altitude_m:.2f} m")
            await asyncio.sleep(1)
            break

    # Calculate average for stability
    if len(stable_altitudes) == stability_duration:
        average_alt = sum(stable_altitudes) / stability_duration
        logging.info(f"✅ Stable altitude recorded: {average_alt:.2f} m")
        return average_alt
    else:
        logging.warning("⚠️ Could not capture stable readings.")
        return None

async def main():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    logging.info("🔌 Connecting to drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            logging.info("✅ Drone connected.")
            break

    logging.info("📦 Lift the drone manually and hold it at the desired altitude...")
    await asyncio.sleep(5)  # Give time to lift the drone

    saved_altitude = await get_stable_altitude(drone)

    if saved_altitude is not None:
        with open("saved_altitude.txt", "w") as file:
            file.write(f"{saved_altitude:.2f}")
        logging.info("📁 Altitude saved to 'saved_altitude.txt'")

if __name__ == "__main__":
    asyncio.run(main())
