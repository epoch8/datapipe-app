import asyncio
import websockets
import json
import rich
import httpx
from tqdm import tqdm

ws_endpoint = "ws://localhost:3001/api/v1alpha2/ws/transform/agg_profile_e3446323b3/run-status"
start_endpoint = "http://localhost:3001/api/v1alpha2/transform/run"


async def main():
    async with httpx.AsyncClient() as client:
        response = await client.post(start_endpoint, json={"transform": "agg_profile_e3446323b3"})
        response_json = response.json()
        if response_json["status"] == "no changes":
            return
        rich.print(response_json)
        assert response.status_code == 200
    async with websockets.connect(ws_endpoint) as websocket:
        result = await websocket.recv()
        data = json.loads(result)
        prev = data["processed"]
        with tqdm(total=data["total"], initial=prev) as t:
            while True:
                result = await websocket.recv()
                data = json.loads(result)
                t.total = data["total"]
                t.update(data["processed"] - prev)
                prev = data["processed"]
                if data["status"] == "finished":
                    break


if __name__ == "__main__":
    asyncio.run(main())
