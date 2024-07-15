import asyncio
import json

import websockets
from tqdm import tqdm

ws_endpoint = "ws://localhost:3001/api/v1alpha2/ws/transform/agg_profile_e3446323b3/run-status"


async def main():
    async with websockets.connect(ws_endpoint) as websocket:
        await websocket.send(json.dumps({"operation": "run-step", "transform": "agg_profile_e3446323b3"}))
        result = await websocket.recv()
        data = json.loads(result)
        if data["status"] == "starting":
            result = await websocket.recv()
            data = json.loads(result)
        if data["status"] == "finished":
            print("Finished")
            return
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
        print("Finished")


if __name__ == "__main__":
    asyncio.run(main())
