import asyncio
import json
from typing import List, Tuple, Optional

import httpx
import netifaces

def get_network_prefix() -> str:
    """Get the network prefix from the default gateway."""
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET][0]
    octets = default_gateway.split(".")
    network_prefix = ".".join(octets[:3])
    return network_prefix

async def fetch_tasmota_device(link: int) -> Optional[Tuple[str, str, str]]:
    """Fetch the Tasmota device status from a given IP link."""
    network_prefix = get_network_prefix()
    ip = f"{network_prefix}.{link}"
    endpoint = f"http://{ip}/cm?cmnd=STATUS"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)
            startstr = '{"Status":{"Module"'
            if response.text.startswith(startstr):
                data = json.loads(response.text)
                device_name = data.get("Status", {}).get("DeviceName", "Unknown")
                friendly_name = data.get("Status", {}).get("FriendlyName", ["Unknown"])[0]
                return ip, device_name, friendly_name
    except (httpx.RequestError, json.JSONDecodeError, TimeoutError):
        pass
    return None

async def main(raw_data: bool = False) -> List[Tuple[str, str, str]]:
    """
    Discover Tasmota devices on the local network.

    If `raw_data` is True, return a list of discovered Tasmota devices.
    Otherwise, print a formatted table of discovered devices and return an empty list.
    """
    tasks = [fetch_tasmota_device(i) for i in range(1, 256)]
    tasmota_devices = await asyncio.gather(*tasks)
    tasmota_devices = [dev for dev in tasmota_devices if dev]

    if raw_data:
        return tasmota_devices

    print("\nTasmota devices found:")

    if tasmota_devices:
        # Calculate the maximum lengths for each column
        max_ip_length = max(len(ip) for ip, _, _ in tasmota_devices)
        max_device_name_length = max(len(device_name) for _, device_name, _ in tasmota_devices)
        max_friendly_name_length = max(len(friendly_name) for _, _, friendly_name in tasmota_devices)

        # Print the formatted table
        for i, (ip, device_name, friendly_name) in enumerate(tasmota_devices, start=1):
            print(f"{i:2} | IP: {ip:{max_ip_length}} | Device Name: {device_name:{max_device_name_length}} | Friendly Name: {friendly_name:{max_friendly_name_length}}")
    else:
        print("No Tasmota devices found.")

    return []

if __name__ == "__main__":
    print("Please wait, this might take a while.")
    data = asyncio.run(main(raw_data=False))
    if data:
        print(data)