import asyncio
import json
import sys
import os

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

sys.path.append(os.path.join(os.path.dirname(__file__), "edge_node"))
from edge import run_edge_node

app = FastAPI()

# We'll create this dashboard.html file in the next instruction
app.mount("/static", StaticFiles(directory="dashboard"), name="static")

# This lets the edge node "pause" and wait for a browser click instead of input()
resume_event = asyncio.Event()


@app.get("/")
async def get_dashboard():
    with open(os.path.join("dashboard", "dashboard.html")) as f:
        return HTMLResponse(f.read())


@app.post("/resume")
async def resume():
    resume_event.set()
    return {"status": "resumed"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Dashboard connected. Starting simulation...")

    loop = asyncio.get_event_loop()

    def run_simulation_sync():
        """
        Runs the (synchronous) edge node generator in a background thread,
        sending each reading to the browser via the event loop.
        """
        for reading in run_edge_node():
            # Send this reading to the browser
            asyncio.run_coroutine_threadsafe(
                websocket.send_text(json.dumps(reading)), loop
            )

            # If it's a Tier 1 event, wait here for the browser to click "resume"
            if reading["tier"] == 1:
                resume_event.clear()
                asyncio.run_coroutine_threadsafe(
                    websocket.send_text(json.dumps({"type": "PAUSE_EVENT", "reading": reading})),
                    loop
                ).result()

                # Block this background thread until resume_event is set
                future = asyncio.run_coroutine_threadsafe(resume_event.wait(), loop)
                future.result()  # blocks here until /resume is called

    await loop.run_in_executor(None, run_simulation_sync)
    await websocket.send_text(json.dumps({"type": "MATCH_ENDED"}))
    print("Match ended.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)