import httpx

async def fetch_data():
    ip = "192.168.178.120"
    endpoint_status = f"http://{ip}/cm?cmnd=STATUS"
    endpoint_statusnet = f"http://{ip}/cm?cmnd=STATUS 5"

    try:
        async with httpx.AsyncClient() as client:
            response_status = await client.get(endpoint_status)
            response_statusnet = await client.get(endpoint_statusnet)
            
            # Check if the request was successful
            if response_status.status_code == 200:
                print("Status response received:", response_status.text)
            else:
                print("Status request failed with status code:", response_status.status_code)
            
            if response_statusnet.status_code == 200:
                print("Statusnet response received:", response_statusnet.text)
            else:
                print("Statusnet request failed with status code:", response_statusnet.status_code)
    except httpx.HTTPError as exc:
        print("HTTP error occurred:", exc)
    except Exception as exc:
        print("An unexpected error occurred:", exc)

# Call the async function
import asyncio
asyncio.run(fetch_data())
