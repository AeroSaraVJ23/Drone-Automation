import asyncio
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="serial:///dev/ttyACM0:57600")

    async for health in drone.telemetry.health():
        print(
            f"Gyro ok={health.is_gyrometer_calibration_ok}, "
            f"Accel ok={health.is_accelerometer_calibration_ok}, "
            f"Mag ok={health.is_magnetometer_calibration_ok}, "
            f"LocalPos ok={health.is_local_position_ok}, "
            f"GlobalPos ok={health.is_global_position_ok}, "
            f"Home ok={health.is_home_position_ok}, "
            f"Armable = {health.is_armable}"
        )
