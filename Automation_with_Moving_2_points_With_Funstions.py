import asyncio
import logging
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

# ================================
# CONNECTION AND HEALTH CHECKS
# ================================

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
    logging.info("🩺 Checking gyroscope and accelerometer health...")
    async for health in drone.telemetry.health():
        if health.is_gyrometer_calibration_ok and health.is_accelerometer_calibration_ok:
            logging.info("✅ Gyroscope and accelerometer OK.")
            break
        await asyncio.sleep(1)

async def check_gps_health(drone: System):
    logging.info("📡 Checking GPS and home position status...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            logging.info("✅ GPS and home position OK.")
            break
        await asyncio.sleep(1)

async def check_rc_signal(drone: System):
    logging.info("🎮 Checking RC signal...")
    async for rc_status in drone.telemetry.rc_status():
        if rc_status.is_available:
            logging.info(f"✅ RC signal detected. Strength: {rc_status.signal_strength_percent:.1f}%")
            break
        await asyncio.sleep(1)

async def check_armable(drone: System):
    async for is_armed in drone.telemetry.armed():
        if not is_armed:
            logging.info("✅ Drone is currently disarmed and ready to arm.")
            break
        await asyncio.sleep(1)

# ================================
# ACTIONS
# ================================

async def arm_drone(drone: System):
    try:
        await drone.action.arm()
        logging.info("🚀 Drone armed.")
    except Exception as e:
        logging.error(f"❌ Failed to arm: {e}")

async def takeoff(drone: System, altitude=2.0):
    try:
        logging.info(f"🛫 Taking off to {altitude}m...")
        await drone.action.set_takeoff_altitude(altitude)
        await drone.action.takeoff()
        await asyncio.sleep(5)
    except Exception as e:
        logging.error(f"❌ Takeoff failed: {e}")

async def land(drone: System):
    logging.info("🛬 Landing...")
    await drone.action.land()

async def move_ned(drone: System, north=0.0, east=0.0, down=0.0, duration=4):
    try:
        velocity = VelocityNedYaw(north, east, down, 0.0)
        await drone.offboard.set_velocity_ned(velocity)
        logging.info(f"➡️ Moving NED: N={north}, E={east}, D={down} for {duration}s")

        try:
            await drone.offboard.start()
        except:
            await drone.offboard.stop()
            await drone.offboard.start()

        await asyncio.sleep(duration)
        await drone.offboard.stop()
    except Exception as e:
        logging.error(f"❌ Movement failed: {e}")

# ================================
# Log
# ================================

async def monitor_status_text(drone: System):
    async for status_text in drone.telemetry.status_text():
        level = status_text.type
        text = status_text.text

        if level.name in ["ERROR", "CRITICAL", "WARNING"]:
            logging.warning(f"📣 [{level.name}] {text}")
        else:
            logging.info(f"ℹ️ [{level.name}] {text}")

# ================================
# GPS
# ================================
async def get_gps_coordinates(drone: System):
    async for position in drone.telemetry.position():
        logging.info(f"📍 GPS Position: Latitude={position.latitude_deg:.7f}, "
                     f"Longitude={position.longitude_deg:.7f}, "
                     f"Altitude={position.relative_altitude_m:.2f}m")
        break  # Only get one update


# ================================
# Altitude
# ================================

async def get_absolute_altitude(drone: System):
    async for pos in drone.telemetry.position():
        return pos.absolute_altitude_m




# ================================
# Location Moving
# ================================
async def go_to_gps_location1(drone: System):
    lat = 7.2530242
    lon = 80.5922737

    # Get current absolute altitude to maintain level flight
    abs_alt = await get_absolute_altitude(drone)

    try:
        logging.info(f"✈️ Going to Latitude={lat}, Longitude={lon}, Altitude={abs_alt:.2f}")
        await drone.action.goto_location(lat, lon, abs_alt, 0.0)
        logging.info("📌 Navigation command sent. Waiting to reach...")
    except Exception as e:
        logging.error(f"❌ Failed to navigate: {e}")

async def go_to_gps_location2(drone: System):
    lat = 7.2530244
    lon = 80.5924079

    # Get current absolute altitude to maintain level flight
    abs_alt = await get_absolute_altitude(drone)

    try:
        logging.info(f"✈️ Going to Latitude={lat}, Longitude={lon}, Altitude={abs_alt:.2f}")
        await drone.action.goto_location(lat, lon, abs_alt, 0.0)
        logging.info("📌 Navigation command sent. Waiting to reach...")
    except Exception as e:
        logging.error(f"❌ Failed to navigate: {e}")


# ================================
# Outside Data capturing - shell commands
# ================================
async def run_sensor_script():
    """
    Asynchronously runs a predefined Python script and logs output/errors.
    """
    process = await asyncio.create_subprocess_shell(
        "python3 /home/raspig11/Caputuring/BLE/client.py",  # Replace with actual script
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logging.info("✅ Script executed successfully.")
        logging.debug(stdout.decode())
    else:
        logging.error(f"❌ Script failed with return code {process.returncode}.")
        logging.error(f"Stdout: {stdout.decode()}")
        logging.error(f"Stderr: {stderr.decode()}")

async def run_camera_script():
    """
    Asynchronously runs a predefined Python script and logs output/errors.
    """
    process = await asyncio.create_subprocess_shell(
        "python3 /home/raspig11/Caputuring/Camera/capture3.py",  # Replace with actual script
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        logging.info("✅ Script executed successfully.")
        logging.debug(stdout.decode())
    else:
        logging.error(f"❌ Script failed with return code {process.returncode}.")
        logging.error(f"Stdout: {stdout.decode()}")
        logging.error(f"Stderr: {stderr.decode()}")




# ================================
# MAIN MENU
# ================================

async def main():
    drone = await connect_drone()
    await check_basic_health(drone)
    await check_gps_health(drone)
    await check_rc_signal(drone)
    await check_armable(drone)

    # Start background task to monitor Pixhawk status messages
    asyncio.create_task(monitor_status_text(drone))

    while True:
        print("\n=== DRONE MENU ===")
        print("1. Arm")
        print("2. Takeoff to 2m")
        print("3. Move forward (pitch +2m)")
        print("4. Move backward (pitch -2m)")
        print("5. Move left (roll -2m)")
        print("6. Move right (roll +2m)")
        print("7. Land")
        print("8. Get GPS coordinates")
        print("9. Go to GPS location Sensor")
        print("10. Go to GPS location Land")
        print("11. Sensor Reading")
        print("12. Image Capturing")
        print("13. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            await arm_drone(drone)
        elif choice == "2":
            await takeoff(drone)
        elif choice == "3":
            await move_ned(drone, north=0.5)
        elif choice == "4":
            await move_ned(drone, north=-0.5)
        elif choice == "5":
            await move_ned(drone, east=-0.5)
        elif choice == "6":
            await move_ned(drone, east=0.5)
        elif choice == "7":
            await land(drone)
        elif choice == "8":
            await get_gps_coordinates(drone)
        elif choice == "9":
            await go_to_gps_location1(drone)
        elif choice == "10":
            await go_to_gps_location2(drone)
        elif choice == "11":
            logging.info("▶️ Running Sensor script...")
            await run_sensor_script()
        elif choice == "12":
            logging.info("▶️ Running Camera Capture script...")
            await run_camera_script()
        elif choice == "13":
            print("🔚 Exiting control...")
            break
          
        else:
            print("❌ Invalid choice.")




if __name__ == "__main__":
    asyncio.run(main())
