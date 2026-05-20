import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://127.0.0.1:8001/api/recognition/ws') as ws:
            print('Connected!')
            await ws.send('data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=')
            res = await ws.recv()
            print('Received response!')
            print(res[:50])
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
