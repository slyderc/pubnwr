#!/usr/bin/env python3
"""
PubNWR v2.0 - Now Wave Radio's music player automation script
Main entry point for the application.
"""

import os
import sys
import time
import json
import signal
import logging
from pathlib import Path

from handlers.config_handler import ConfigHandler
from handlers.database_handler import DatabaseHandler
from handlers.playout_handler import PlayoutData, process_new_track_data
from handlers.file_handler import start_file_watch

DEFAULT_CONFIG_FILE = "/etc/pubnwr_MYRIAD.ini"

def reload_config(signal, frame):
    """Reload configuration when SIGHUP is received"""
    global config_handler
    try:
        config_handler.reload()
        logging.info(f"Reloaded configuration: {config_handler.config_file}")
    except Exception as e:
        logging.error(f"Failed to reload configuration: {e}", exc_info=True)

def reload_playout_file(playout_data, state, db_handler, content=None):
    """
    Reload and process the playout file
    
    Args:
        playout_data: PlayoutData instance
        state: State dictionary
        db_handler: Database handler instance
        content: Optional file content from file watcher
    """
    try:
        if content:
            # Use provided content if available
            playout_data.data = json.loads(content)
        else:
            # Fall back to reading file directly
            playout_data.data = playout_data._load_playout_json()
            
        logging.debug(f"Loaded play-out data: {playout_data}")
        
        process_new_track_data(playout_data, state, db_handler, config_handler)
        
        state["last_processed_time"] = time.time()
        state["current_track_duration"] = int(playout_data.data.get("duration", 0))
        
    except Exception as e:
        logging.error(f"Error processing playout data: {e}", exc_info=True)

def main(db_handler):
    playout_data = PlayoutData(config_handler.pub_json_file, config_handler.script_home)
    
    state = {
        "last_processed_time": time.time(),
        "current_track_duration": int(playout_data.data.get("duration", 0))
    }
    
    logging.info("Starting initial JSON processing.")
    reload_playout_file(playout_data, state, db_handler)
    
    playout_file_path = Path(config_handler.pub_json_file)
    logging.info(f"Starting file watch on: {playout_file_path}")
    
    # Pass config to file watch function
    start_file_watch(
        playout_file_path=playout_file_path,
        reload_callback=lambda content: reload_playout_file(playout_data, state, db_handler),
        state=state,
        config=config_handler
    )

if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) == 2 else DEFAULT_CONFIG_FILE
    if not os.path.isfile(config_file) or not os.access(config_file, os.R_OK):
        print(f'*** ERROR: Cannot open config. file: {config_file}')
        exit(1)

    config_handler = ConfigHandler(config_file)
    db_handler = DatabaseHandler(config_handler.db_file)
    
    signal.signal(signal.SIGHUP, reload_config)

    try:
        main(db_handler)
    except Exception as err:
        logging.exception("\n****** CRASHED ******\n%s", err)
        with open(config_handler.pub_json_file, 'r', encoding='utf-8') as file:
            logging.error(f"Playout JSON file contents: {file.read()}")
        exit(2)

