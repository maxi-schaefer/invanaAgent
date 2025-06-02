# scripts.py
import os
import json
import logging

SCRIPTS_FILE = "./scripts.json"

def load_scripts():
    if not os.path.exists(SCRIPTS_FILE):
        return []
    try:
        with open(SCRIPTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to open scripts: {e}")
        return []
    
def save_scripts(scripts):
    try:
        with open(SCRIPTS_FILE, "w") as f:
            json.dump(scripts, f, indent=4)
        logging.info(f"Saved {len(scripts)} scripts to {SCRIPTS_FILE}")
    except Exception as e:
        logging.error(f"Failed to save scripts: {e}")

def replace_scripts(scripts):
    save_scripts(scripts)
    logging.info(f"Replaced all scripts with {len(scripts)} items.")

def add_script(script):
    scripts = load_scripts()
    scripts.append(script)
    save_scripts(scripts)
    logging.info(f"Script added: {script.get('name', 'Unnamed')}")