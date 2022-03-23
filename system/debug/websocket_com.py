import asyncio
import websockets

# "wss://ec2-18-191-244-170.us-east-2.compute.amazonaws.com/socketio"

async def hello():
    async with websockets.connect("wss://ec2-18-191-244-170.us-east-2.compute.amazonaws.com/socketio") as websocket:
        await websocket.send("0,0")
        await print(websocket.recv())

asyncio.run(hello())