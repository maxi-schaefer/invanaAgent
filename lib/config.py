# config.py
import os
import json

CONFIG_PATH = "./config.json"
AGENT_ID = None

def load_config():
    global AGENT_ID
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({}, f)
        return {}

    with open(CONFIG_PATH, "r") as f:
        data = json.load(f)
        if "agent_id" in data:
            AGENT_ID = data["agent_id"]
            print(f"[config] Loaded agent_id from config: {AGENT_ID}")
        return data
    
def reset_agent():
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
        print("Config deleted due to denial.")
    set_agent_id(None)

def save_config(data):
    if AGENT_ID:
        data["agent_id"] = AGENT_ID
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def get_config_value(key, default=None):
    config = load_config()
    return config.get(key, default)

def set_agent_id(agent_id):
    global AGENT_ID
    AGENT_ID = agent_id

def get_agent_id():
    global AGENT_ID
    return AGENT_ID
