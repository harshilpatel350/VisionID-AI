import asyncio
import websockets
import base64
import cv2
import numpy as np

async def test():
    # Create a simple valid JPEG image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    if not ok:
        print("Failed to encode")
        return
    
    b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
    payload = f"data:image/jpeg;base64,{b64}"
    
    try:
        async with websockets.connect('ws://127.0.0.1:8001/api/recognition/ws') as ws:
            print('Connected!')
            await ws.send(payload)
            res = await ws.recv()
            print('Response received!')
            print(res[:100])
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
