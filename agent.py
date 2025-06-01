import os
import json
import asyncio
import socket
import platform
import logging
import websockets
from lib.config import load_config, save_config, get_config_value, set_agent_id, get_agent_id, reset_agent

# Configure logging
logging.basicConfig(
    filename="agent.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DEFAULT_WS_URL = "localhost"
DEFAULT_WS_PORT = 8080

AGENT_INFO = {
    "name": socket.gethostname(),
    "hostname": socket.gethostname(),
    "ip": socket.gethostbyname(socket.gethostname()),
    "environment": "",
    "os": platform.system().lower(),
    "services": 2,
    "version": "1.0.0"
}

def build_message(msg_type, payload=None):
    return json.dumps({
        "type": msg_type,
        "payload": payload
    })

def get_server_ws_url():
    config = load_config()
    url = config.get("serverUrl", DEFAULT_WS_URL)
    port = config.get("serverPort", DEFAULT_WS_PORT)

    url = url.replace("http://", "").replace("https://", "")
    return f"ws://{url}:{port}/ws/agent"

def update_connection_settings(new_config):
    current_config = load_config()
    updated = False
    restart_required = False

    for key in ["serverUrl", "serverPort"]:
        if key in new_config and new_config[key] != current_config.get(key):
            logger.info(f"Updating {key}: {current_config.get(key)} → {new_config[key]}")
            current_config[key] = new_config[key]
            restart_required = True
            updated = True

    for key, value in new_config.items():
        if key not in ["serverUrl", "serverPort"] and current_config.get(key) != value:
            logger.info(f"Updating config key: {key} = {value}")
            current_config[key] = value
            updated = True

    if updated:
        save_config(current_config)
        logger.info("Configuration updated.")

    if restart_required:
        logger.warning("Server connection settings changed. Restarting agent...")
        os._exit(2)

send_queue = asyncio.Queue()

async def register_agent(ws):
    if get_agent_id():
        logger.info(f"Using existing agent_id: {get_agent_id()}")
        return

    logger.info("Registering agent...")
    await ws.send(build_message("REGISTER", AGENT_INFO))
    msg = await ws.recv()

    if msg.startswith("REGISTERED: "):
        agent_id = msg.replace("REGISTERED: ", "").strip()
        set_agent_id(agent_id)
        logger.info(f"Registered with ID: {agent_id}")

        config = load_config()
        config["agent_id"] = agent_id
        save_config(config)
    else:
        logger.error("Unexpected registration response: " + msg)
        raise Exception("Unexpected registration response: " + msg)

async def heartbeat_task():
    while True:
        agent_id = get_agent_id()
        agent_token = get_config_value("token")

        if agent_id and agent_token:
            payload = {
                "id": agent_id,
                "token": agent_token
            }
            await send_queue.put(build_message("HEARTBEAT", payload))
        else:
            logger.warning("Skipping heartbeat: agent_id or token not set.")
        
        await asyncio.sleep(10)

async def sender(ws):
    while True:
        msg = await send_queue.get()
        await ws.send(msg)

async def receiver(ws):
    while True:
        msg = await ws.recv()
        try:
            config = json.loads(msg)
            logger.info(f"Received config: {config}")
            update_connection_settings(config)
            save_config(config)
        except json.JSONDecodeError:
            if msg == "HEARTBEAT_ACK":
                logger.info("Heartbeat acknowledged.")
            elif msg == "HEARTBEAT_DENY":
                logger.warning("Heartbeat denied. Agent might not be accepted yet.")
            elif msg == "AUTH_DENIED":
                logger.error("Auth denied. Check your token.")
            elif msg == "DENIED":
                logger.error("Agent has been denied. Cleaning up...")
                reset_agent()
                await asyncio.sleep(1)
                os._exit(1)
            else:
                logger.warning(f"Unknown message: {msg}")

async def agent_lifecycle():
    load_config()
    while True:
        try:
            ws_url = get_server_ws_url()
            async with websockets.connect(ws_url) as ws:
                logger.info(f"Connected to WebSocket server at {ws_url}")
                await register_agent(ws)

                await asyncio.gather(
                    sender(ws),
                    receiver(ws),
                    heartbeat_task()
                )
        except Exception as e:
            logger.error(f"Connection failed or lost: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(agent_lifecycle())
