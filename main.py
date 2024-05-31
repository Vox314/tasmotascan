import httpx, json, asyncio, netifaces

def get_network_prefix():
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET][0]

    octets = default_gateway.split(".")

    # Join the first three octets to form the network prefix
    network_prefix = ".".join(octets[:3])

    return network_prefix

async def fetch_tasmota_device(link):
    try:
        endpoint = f"http://{get_network_prefix()}.{link}/cm?cmnd=STATUS"
        ip = f"{get_network_prefix()}.{link}"
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint)

            # Check if the response starts with the expected string
            startstr = '{"Status":{"Module"'
            if response.text.startswith(startstr):
                data = json.loads(response.text)
                device_name = data.get("Status", {}).get("DeviceName", "Unknown")
                friendly_name = data.get("Status", {}).get("FriendlyName", ["Unknown"])[0]
                return ip, device_name, friendly_name
    except (httpx.RequestError, json.JSONDecodeError, TimeoutError) as e:
        # print(f"Request Error occurred for {ip}: {e}") # Uncomment to see full request information
        return None

async def main(raw_data: bool=False) -> list:
    """
    If `raw_data` is set to `True`,\ 
    this function will return a `list` of `tasmota_devices` on the local network.

    Else it will just print out the preformatted table and return an empty string `''`.
    """
    tasks = [fetch_tasmota_device(i) for i in range(1, 256)]
    tasmota_devices = await asyncio.gather(*tasks)
    tasmota_devices = [dev for dev in tasmota_devices if dev]  # Remove None results

    if raw_data==True:
        return tasmota_devices

    print("\nTasmota devices found:")

    # Calculate the maximum lengths for each column
    max_ip_length = max(len(ip) for ip, _, _ in tasmota_devices)
    max_device_name_length = max(len(device_name) for _, device_name, _ in tasmota_devices)
    max_friendly_name_length = max(len(friendly_name) for _, _, friendly_name in tasmota_devices)

    # Print the formatted table
    for i, (ip, device_name, friendly_name) in enumerate(tasmota_devices, start=1):
        print(f"{i:2} | IP: {ip:{max_ip_length}} | Device Name: {device_name:{max_device_name_length}} | Friendly Name: {friendly_name:{max_friendly_name_length}}")

    return '' # Returns empty string instead of None

if __name__ == "__main__":
    print("Please wait, this might take a while.")
    data = asyncio.run(main(raw_data=False))
    print(data)