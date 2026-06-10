import asyncio
import json
import math

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer

import threading
import websockets

OSC_PORT = 9000
WS_PORT = 8767

clients = set()
loop = None


def marker_handler(address, *args):

    marker = {
        "id": int(args[0]),

        "t_x": round(args[1], 4),
        "t_y": round(args[2], 4),
        "t_z": round(args[3], 4),

        "angle_x": round(math.degrees(args[4]), 1),
        "angle_y": round(math.degrees(args[5]), 1),
        "angle_z": round(math.degrees(args[6]), 1)
    }

    msg = json.dumps(marker)

    if loop is not None:
        asyncio.run_coroutine_threadsafe(
            broadcast(msg),
            loop
        )


async def broadcast(message):

    if not clients:
        return

    dead = []

    for ws in clients:
        try:
            await ws.send(message)
        except:
            dead.append(ws)

    for ws in dead:
        clients.remove(ws)


async def websocket_handler(websocket):

    clients.add(websocket)

    print("TurboWarp connected")

    try:
        async for msg in websocket:
            print("TW:", msg)

    finally:
        clients.remove(websocket)


def osc_thread():

    dispatcher = Dispatcher()
    dispatcher.map("/marker", marker_handler)

    server = ThreadingOSCUDPServer(
        ("127.0.0.1", OSC_PORT),
        dispatcher
    )

    print(f"OSC listening on {OSC_PORT}")

    server.serve_forever()


async def main():

    global loop

    loop = asyncio.get_running_loop()

    threading.Thread(
        target=osc_thread,
        daemon=True
    ).start()

    await websockets.serve(
        websocket_handler,
        "localhost",
        WS_PORT
    )

    print(f"WebSocket: ws://localhost:{WS_PORT}")

    await asyncio.Future()


asyncio.run(main())