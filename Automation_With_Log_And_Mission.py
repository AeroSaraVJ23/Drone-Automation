
import asyncio
import logging
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
from mavsdk.mission import MissionItem, MissionPlan

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
# Missions
# ================================

# Coordinates: (latitude, longitude, relative_altitude)
WAYPOINTS = [
    (7.253035, 80.592398, 2),  # WP1
    (7.253039, 80.592193, 2),  # WP2
    (7.253035, 80.592398, 2),  # WP3 - Final WP
]

async def build_mission_plan() -> MissionPlan:
    mission_items = []

    for i, (lat, lon, alt) in enumerate(WAYPOINTS):
        hold_time = 20  # seconds

        mission_items.append(MissionItem(
            latitude_deg=lat,
            longitude_deg=lon,
            relative_altitude_m=alt,
            speed_m_s=2.0,
            is_fly_through=False,
            gimbal_pitch_deg=0.0,
            gimbal_yaw_deg=0.0,
            camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=hold_time,
            camera_photo_interval_s=0.0,  # No photo interval
            acceptance_radius_m=1.0,      # Acceptable distance from WP
            yaw_deg=0.0,                  # No specific yaw
            camera_photo_distance_m=0.0,  # Not used
            vehicle_action=MissionItem.VehicleAction.NONE
        ))

    return MissionPlan(mission_items)

  

async def run_mission(drone: System):
    mission_plan = await build_mission_plan()

    logging.info("📤 Uploading mission...")
    await drone.mission.set_return_to_launch_after_mission(False)
    await drone.mission.upload_mission(mission_plan)

    logging.info("🚀 Arming drone...")
    await drone.action.arm()

    await takeoff(drone, altitude=2.0)

    logging.info("🛫 Starting mission...")
    await drone.mission.start_mission()

    while True:
        async for mission_progress in drone.mission.mission_progress():
            current = mission_progress.current
            total = mission_progress.total
            logging.info(f"📍 Mission progress: {current}/{total}")
            break
        if await drone.mission.is_mission_finished():
            break
        await asyncio.sleep(1)

    logging.info("🪂 Mission complete. Initiating landing...")
    await drone.action.land()

    await asyncio.sleep(10)

    async for is_armed in drone.telemetry.armed():
        if is_armed:
            logging.info("🔧 Disarming...")
            await drone.action.disarm()
        break





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
        print("8.Mission")
        print("9. Exit")

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
          await run_mission(drone)
        elif choice == "9":
            print("🔚 Exiting control...")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    asyncio.run(main())
