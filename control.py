import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("✅ Drone discovered!")
            break

    print("Waiting for global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("✅ Global position ready")
            break

    print("-- Arming")
    await drone.action.arm()
    print("✅ Armed!")

if __name__ == "__main__":
    asyncio.run(main())
