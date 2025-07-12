import struct
import asyncio
from bleak import BleakClient
import sys
import requests

# URL and headers for sending data
url = "https://skytimages.pagekite.me/sensor-readings"
headers = {
    "Authorization": "Bearer z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4j3i2h1g0f9e8d7c6b5a4",
    "Content-Type": "application/json"
}

# ✅ Decoding function
def decode_soil_sensor_data(transmit_data):
    if not isinstance(transmit_data, bytes):
        transmit_data = bytes(transmit_data)

    if len(transmit_data) != 12:
        raise ValueError("Transmit data must be 12 bytes long")

    temperature = struct.unpack('>h', transmit_data[0:2])[0] / 10.0
    ph = struct.unpack('>h', transmit_data[2:4])[0] / 10.0
    nitrogen = struct.unpack('>H', transmit_data[4:6])[0]
    phosphorus = struct.unpack('>H', transmit_data[6:8])[0]
    potassium = struct.unpack('>H', transmit_data[8:10])[0]
    dht_humidity = struct.unpack('>h', transmit_data[10:12])[0] * 0.1

    return {
        'Temperature °C': temperature,
        'pH': ph,
        'Nitrogen (mg/kg)': nitrogen,
        'Phosphorus (mg/kg)': phosphorus,
        'Potassium (mg/kg)': potassium,
        'Air Humidity (Relative Humidity %)': dht_humidity
    }

# ✅ BLE reading and HTTP POST
async def get_data(mac, char_uuid, node_id):
    decoded_data = {}

    try:
        async with BleakClient(mac) as client:
            data = await client.read_gatt_char(char_uuid)
            decoded_data = decode_soil_sensor_data(data)
            print("[DEBUG] Decoded data:", decoded_data)
    except Exception as e:
        print(f"[ERROR] Failed to read from BLE device: {e}")
        return

    payload = {
        "nodeId": node_id,
        "temperature": decoded_data['Temperature °C'],
        "humidity": decoded_data['Air Humidity (Relative Humidity %)'],
        "ph": decoded_data['pH'],
        "n": decoded_data['Nitrogen (mg/kg)'],
        "p": decoded_data['Phosphorus (mg/kg)'],
        "k": decoded_data['Potassium (mg/kg)'],
        "battery": 95  # You can replace with actual reading
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("[INFO] Status code:", response.status_code)
        print("[INFO] Response:", response.text)
    except Exception as e:
        print(f"[ERROR] Failed to send POST request: {e}")

# ✅ Argument extraction and run
async def main():
    if len(sys.argv) != 4:
        print("Usage: python script.py <node_id> <MAC> <char_UUID>")
        return

    node_id = sys.argv[1]
    mac = sys.argv[2]
    char_uuid = sys.argv[3]

    await get_data(mac, char_uuid, node_id)

# ✅ Entry point
if __name__ == "__main__":
    asyncio.run(main())
