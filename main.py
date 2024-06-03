import asyncio
import json
from typing import Dict, Tuple, Optional

import httpx
import netifaces

def get_network_prefix() -> str:
    """Get the network prefix from the default gateway."""
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET][0]
    octets = default_gateway.split(".")
    network_prefix = ".".join(octets[:3])
    return network_prefix

async def fetch_tasmota_device(link: int) -> Optional[Tuple[str, str, str, str, str]]:
    """Fetch the Tasmota device status from a given IP link."""
    network_prefix = get_network_prefix()
    ip = f"{network_prefix}.{link}"
    endpoint_status = f"http://{ip}/cm?cmnd=STATUS"
    endpoint_statusnet = f"http://{ip}/cm?cmnd=STATUS 5"
    
    try:
        async with httpx.AsyncClient() as client:
            response_status = await client.get(endpoint_status)
            startstr_status = '{"Status":{"Module"'

            if response_status.text.startswith(startstr_status):
                data = json.loads(response_status.text)
                device_name = data.get("Status", {}).get("DeviceName", "Unknown")
                friendly_name = data.get("Status", {}).get("FriendlyName", ["Unknown"])[0]
                topic = data.get("Status", {}).get("Topic", ["Unknown"])

                response_statusnet = await client.get(endpoint_statusnet)
                startstr_statusnet = '"StatusNET":{"Hostname"'
                if response_statusnet.text.find(startstr_statusnet):
                    data = json.loads(response_statusnet.text)
                    mac = data.get("StatusNET", {}).get("Mac", "Unknown")
                    host_name = data.get("StatusNET", {}).get("Hostname", "Unknown")

                    return ip, mac, host_name, device_name, friendly_name, topic

    except (httpx.RequestError, json.JSONDecodeError, TimeoutError):
        pass
    return None

async def main(raw_data: bool = False) -> Dict[str, str]:
    """
    Discover Tasmota devices on the local network.

    If `raw_data` is True, return a json dataset of discovered Tasmota devices.
    Otherwise, print a formatted table of discovered devices and return an empty dictionary.
    """
    tasks = [fetch_tasmota_device(i) for i in range(1, 256)]
    tasmota_devices = await asyncio.gather(*tasks)
    tasmota_devices = [dev for dev in tasmota_devices if dev]

    if raw_data:
        formatted_data = {}
        for ip, mac, host_name, device_name, friendly_name, topic in tasmota_devices:
            formatted_data[mac] = {
                'Ip': ip,
                'Hostname': host_name,
                'DeviceName': device_name,
                'FriendlyName': friendly_name,
                'Topic': topic,
            }

            json_data = json.dumps(formatted_data, indent=4)
            with open('devices.json', 'w') as f:
                f.write(json_data)

        return json_data

    print("\nTasmota devices found:")

    if tasmota_devices:
        # Calculate the maximum lengths for each column
        max_mac_length = max(len(mac) for mac, *_ in tasmota_devices)
        max_ip_length = max(len(ip) for _, ip, *_ in tasmota_devices)
        max_host_name_length = max(len(host_name) for _, _, host_name, *_ in tasmota_devices)
        max_device_name_length = max(len(device_name) for *_, device_name, _, _, in tasmota_devices)
        max_friendly_name_length = max(len(friendly_name) for *_, friendly_name, _ in tasmota_devices)
        max_topic_length = max(len(topic) for *_, topic in tasmota_devices)

        # Print the formatted table
        for i, (mac, ip, host_name, device_name, friendly_name, topic) in enumerate(tasmota_devices, start=1):
            print(f"{i:2} | MAC: {mac:{max_mac_length}} | IP: {ip:{max_ip_length}} | Host Name: {host_name:{max_host_name_length}} | Device Name: {device_name:{max_device_name_length}} | Friendly Name: {friendly_name:{max_friendly_name_length}} | Topic: {topic:{max_topic_length}}")
    else:
        print("No Tasmota devices found.")

    return {}

if __name__ == "__main__":
    print("Please wait, this might take a while.")
    data = asyncio.run(main(raw_data=True))
    if data:
        print(data)