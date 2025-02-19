# Joao Oliveira 110532
# Pedro Ponte 98059
# Filipe Posio 80709

import asyncio
import getpass
import json
import os
import logging
import websockets

import digdug_agent
from timeit import default_timer as timer

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        agent = digdug_agent.DigDugAgent()

        times = []
        max_time = 0

        while True:
            try:
                state = json.loads(await websocket.recv())
                start = timer()

                agent.act(state)

                end = timer()

                time = (1000 * (end-start))
                max_time = max(max_time, time)
                times.append(time)
                if time >= 30:
                    print("Total time : %.1f ms" % time)
                    print("---")

                await websocket.send(json.dumps({"cmd": "key", "key": agent.key.value}))

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                print("Average", sum(times)/len(times), "ms")
                print("Highest", max_time, "ms")

                return

loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))