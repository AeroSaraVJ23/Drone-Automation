from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import threading
import subprocess
from pymavlink import mavutil
import sys

# Set your Wi-Fi router's IP address
target_ip = "192.168.1.1"
wifi_check_interval = 5  # seconds
wifi_failure_threshold = 2  # ping failures before landing
stop_threads = False

# Connect to Pixhawk
print("Connecting to vehicle...")
vehicle = connect('/dev/ttyACM0', wait_ready=True, baud=57600)

# --- Wi-Fi monitoring thread (DISABLED for now) ---
# def check_wifi_connection():
#     global stop_threads
#     failure_count = 0
#     while not stop_threads:
#         result = subprocess.run(["ping", "-c", "1", target_ip],
#                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#         if result.returncode == 0:
#             failure_count = 0
#         else:
#             failure_count += 1
#             print(f"[WARN] Wi-Fi ping failed ({failure_count}/{wifi_failure_threshold})")
#             if failure_count >= wifi_failure_threshold:
#                 print("[ALERT] Wi-Fi lost. Landing drone.")
#                 land()
#                 stop_threads = True
#                 sys.exit(1)
#         time.sleep(wifi_check_interval)

# Check for GUIDED mode before any command
def ensure_guided_mode():
    if vehicle.mode.name != "GUIDED":
        print(f"[ERROR] Current flight mode is {vehicle.mode.name}. Switch to GUIDED on RC to use commands.")
        return False
    return True

def arm_and_takeoff(aTargetAltitude):
    if not ensure_guided_mode():
        return

    print("Waiting for vehicle to initialise...")
    while not vehicle.is_armable:
        time.sleep(1)

    print("Arming motors...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print(f"Taking off to {aTargetAltitude} meters!")
    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f" Altitude: {alt:.2f}m")
        if alt >= aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)

def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    if not ensure_guided_mode():
        return

    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_BODY_NED,
        0b0000111111000111,
        0, 0, 0,
        velocity_x, velocity_y, velocity_z,
        0, 0, 0, 0, 0)

    for _ in range(duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)

def descend_to(altitude):
    if not ensure_guided_mode():
        return

    print(f"Descending to {altitude} meter")
    vehicle.simple_goto(LocationGlobalRelative(vehicle.location.global_frame.lat,
                                               vehicle.location.global_frame.lon,
                                               altitude))
    time.sleep(5)

def land():
    print("Landing...")
    vehicle.mode = VehicleMode("LAND")

def main_menu():
    # --- Wi-Fi monitor thread (DISABLED) ---
    # wifi_thread = threading.Thread(target=check_wifi_connection, daemon=True)
    # wifi_thread.start()

    while True:
        print("\n==== DRONE COMMAND MENU ====")
        print("1. Arm and takeoff to 2m")
        print("2. Descend to 1m")
        print("3. Fly forward 2m")
        print("4. Fly backward 2m")
        print("5. Move left 2m")
        print("6. Move right 2m")
        print("7. Land")
        print("8. Exit")
        choice = input("Enter choice: ")

        if stop_threads:
            print("[INFO] Emergency landing triggered. Aborting.")
            break

        if choice == '1':
            arm_and_takeoff(2)
        elif choice == '2':
            descend_to(1)
        elif choice == '3':
            print("Flying forward 2m")
            send_ned_velocity(0.5, 0, 0, 4)
        elif choice == '4':
            print("Flying backward 2m")
            send_ned_velocity(-0.5, 0, 0, 4)
        elif choice == '5':
            print("Moving left 2m")
            send_ned_velocity(0, -0.5, 0, 4)
        elif choice == '6':
            print("Moving right 2m")
            send_ned_velocity(0, 0.5, 0, 4)
        elif choice == '7':
            land()
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice")

    global stop_threads
    stop_threads = True
    print("Closing vehicle connection...")
    vehicle.close()

if __name__ == "__main__":
    main_menu()
