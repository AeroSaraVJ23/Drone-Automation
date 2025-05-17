from mavsdk import System
import asyncio

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("⏳ Connecting...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✅ Drone connected")
            break

    # Optional: skip global position check if no GPS
    print("🚀 Arming drone...")
    await drone.action.arm()
    print("✅ Drone armed!")

asyncio.run(run())
