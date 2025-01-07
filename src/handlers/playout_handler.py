"""
Playout handler for PubNWR
Manages processing of playout JSON data and track information
"""

import json
import logging
import re
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import pytz

from models.track_info import TrackInfo
from services.social_publisher import SocialPublisher, SocialService

class PlayoutData:
    def __init__(self, json_filename: str, script_home: str):
        """
        Initialize playout data handler
        
        Args:
            json_filename: Path to JSON file containing playout data
            script_home: Base directory for script
        """
        self.filename = json_filename
        self.data = self._load_playout_json() or {}
        self.state = {
            "last_program_name": None,
            "program_start_time": None,
            "tracks_played": 0,
            "current_track_duration": self.data.get("duration", 0),
            "last_published_image": None,
            "last_processed_checksum": None,
            "last_processed_time": time.time()
        }

    def load_track_info(self) -> TrackInfo:
        """
        Create TrackInfo instance from current playout data
        
        Returns:
            TrackInfo: Track information object
        """
        return TrackInfo.from_json(self.data)

    def _load_playout_json(self, retries: int = 5, delay: float = 1.0) -> Optional[Dict[str, Any]]:
        """
        Load and parse the playout JSON file
        
        Args:
            retries: Number of retry attempts
            delay: Delay between retries in seconds
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None on error
        """
        attempt = 0
        while attempt < retries:
            try:
                with open(self.filename, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    sanitized_content = self._sanitize_json(content)
                    data = json.loads(sanitized_content)
                    return data
    
            except FileNotFoundError:
                logging.warning(f"File {self.filename} not found. Retrying...")
            except json.JSONDecodeError as e:
                logging.error(f"Unrecoverable JSON error in {self.filename}: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error reading {self.filename}: {e}")
                
            attempt += 1
            time.sleep(delay)
            
        logging.error(f"Failed to load JSON file after {retries} attempts!")
        return None
    
    def _sanitize_json(self, content: str) -> str:
        """
        Sanitize JSON content to handle common issues
        
        Args:
            content: Raw JSON string
            
        Returns:
            str: Sanitized JSON string
        """
        def _fix_values(match):
            key = match.group(1)
            value = match.group(2).replace('\\', r'\\')
            value = value.replace('"', r'\"')
            return f'"{key}": "{value}"'
        
        # Clean up the JSON content
        content = re.sub(r'"([^"]+)": "([^"]+)"', _fix_values, content)
        content = re.sub(r'[\x00-\x1F\x7F]', '', content)
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*\]', ']', content)
        
        return content
                            
    def remove_old_artwork(self, dest_dir: Path) -> None:
        """
        Remove previous artwork file
        
        Args:
            dest_dir: Directory containing artwork files
        """
        previous_artwork = self.state.get("last_published_image")
        if not previous_artwork:
            return
            
        previous_artwork_path = dest_dir / previous_artwork
        
        try:
            if previous_artwork_path.exists():
                previous_artwork_path.unlink()
                logging.info(f"Deleted old artwork file: {previous_artwork_path}")
            else:
                logging.debug(f"No previous artwork file found at {previous_artwork_path}")
        except Exception as e:
            logging.warning(f"Failed to delete previous artwork file: {e}")

    def copy_album_artwork(self, source_dir: Path, dest_dir: Path, config) -> None:
        """
        Copy album artwork to web directory
        
        Args:
            source_dir: Source directory containing artwork
            dest_dir: Destination directory for web access
            config: Configuration instance
        """
        publish_image = self.data.get("publish_image")
        if not publish_image:
            logging.error("No publish_image name available")
            return
        
        # Helper function to copy default image
        def copy_default_image(dest_name: str) -> bool:
            source_file = Path(config.default_img)
            dest_file = dest_dir / dest_name
            
            if not source_file.exists():
                logging.error(f"Default image not found at: {source_file}")
                return False
                
            try:
                logging.info(f"Using default artwork: {source_file} -> {dest_file}")
                shutil.copy(source_file, dest_file)
                return True
            except Exception as e:
                logging.error(f"Failed to copy default artwork: {e}")
                return False
        
        # If using default image
        if publish_image == "default-art.jpg":
            copy_default_image(publish_image)
            return
        
        # Regular artwork handling
        source_image = self.data.get("image", "art-00.jpg")
        source_file = source_dir / source_image
        dest_file = dest_dir / publish_image
        
        try:
            if source_file.exists():
                logging.info(f"Copying album artwork: {source_file} -> {dest_file}")
                shutil.copy(source_file, dest_file)
                try:
                    source_file.unlink()
                    logging.info(f"Deleted source file: {source_file}")
                except Exception as e:
                    logging.warning(f"Failed to delete source file: {e}")
            else:
                logging.warning(f"Source artwork file not found: {source_file}")
                logging.info("Falling back to default artwork")
                # Use the original publish_image name to maintain consistency
                if copy_default_image(publish_image):
                    # Update the data to reflect we're using default image
                    self.data['image'] = 'default-art.jpg'
        except Exception as e:
            logging.error(f"Failed to copy album artwork: {e}")
            # Try to use default image as last resort
            copy_default_image(publish_image)

    def write_playlist_json(self, dest_dir: Path, config) -> None:
        """Write playlist JSON file for website integration"""
        playlist_file = dest_dir / "playlist.json"
        publish_image = self.data.get("publish_image")
        
        if not publish_image:
            logging.error("No publish_image available for playlist JSON")
            return
    
        web_publish_image_path = f"/{config.url_publish_dir}/{publish_image}"
        image_url = f"{config.host_url}/{config.url_publish_dir}/{publish_image}"
    
        try:
            # Don't include empty artist/title in JSON if using default image
            if publish_image == "default-art.jpg":
                playlist_data = {
                    "image": web_publish_image_path,
                    "program_title": self.data.get("program", "Now Wave Radio"),
                    "presenter": self.data.get("presenter", ""),
                    "results": [{"appimage": image_url}]
                }
            else:
                playlist_data = {
                    "artist": self.data.get("artist", "Unknown Artist"),
                    "title": self.data.get("title", "Unknown Title"),
                    "album": self.data.get("album", "Unknown Album"),
                    "publisher": self.data.get("publisher", ""),
                    "ISRC": self.data.get("ISRC", ""),
                    "image": web_publish_image_path,
                    "program_title": self.data.get("program", "Unknown Program"),
                    "presenter": self.data.get("presenter", ""),
                    "start_time": self.data.get("starttime", ""),
                    "duration": int(self.data.get("duration", 0)),
                    "results": [{"appimage": image_url}]
                }
            
            with open(playlist_file, "w", encoding="utf-8") as f:
                json.dump(playlist_data, f, indent=4)
            logging.info(f"Playlist JSON written to {playlist_file}")
            
        except Exception as e:
            logging.error(f"Failed to write playlist JSON: {e}")
        

def process_new_track_data(playout_data: PlayoutData, 
                                 state: dict,
                                 db_handler,
                                 config) -> None:
    """
    Process new track data from playout system
    
    Args:
        playout_data: PlayoutData instance containing track info
        state: State dictionary for tracking status
        db_handler: Database handler instance
        config: Configuration handler instance
    """
    try:
        # Load track info
        now_playing = playout_data.load_track_info()
        
        # Update the playout data with the new publish_image
        playout_data.data['publish_image'] = now_playing.publish_image
        
        # If this isn't a valid song, just update the image and return
        if now_playing.publish_image == "default-art.jpg":
            logging.debug("Non-song content detected, using default image")
            # Process artwork and update web files only
            source_dir = Path(config.script_home)
            dest_dir = Path(config.root_publish_path)
            playout_data.copy_album_artwork(source_dir, dest_dir, config)
            playout_data.write_playlist_json(dest_dir, config)
            return
    
        current_program_name = now_playing.program_title.strip()
        state = playout_data.state
    
        # Generate checksum for current track
        current_checksum = f"{now_playing.artist}:{now_playing.title}"
        
        # Check for duplicate track
        if current_checksum == state.get("last_processed_checksum"):
            logging.debug("No new track detected. Skipping processing.")
            return
        
        # Update state
        state["last_processed_checksum"] = current_checksum
        state["last_processed_time"] = time.time()
        state["current_track_duration"] = now_playing.duration
        
        # Clean up previous artwork
        dest_dir = Path(config.root_publish_path)
        playout_data.remove_old_artwork(dest_dir)
    
        # Format timestamp
        try:
            datetime_obj = datetime.strptime(now_playing.start_time, 
                                          "%Y-%m-%dT%H:%M:%S.%f0Z")
        except ValueError as e:
            logging.warning(f"Invalid start_time format '{now_playing.start_time}'. "
                          f"Using current UTC time. Error: {e}")
            datetime_obj = datetime.utcnow()
    
        # Convert to local timezone
        local_timezone = pytz.timezone(config.timezone)
        datetime_obj = datetime_obj.replace(tzinfo=pytz.utc).astimezone(local_timezone)
        formatted_datetime = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")
    
        # Handle program transitions
        if current_program_name != state["last_program_name"]:
            if state["last_program_name"] is not None:
                logging.info(f"Ending program '{state['last_program_name']}'. "
                           f"Tracks played: {state['tracks_played']}.")
                logging.info(f"Starting new program '{current_program_name}'.")
                state["tracks_played"] = 0
                state["program_start_time"] = time.time()
                state["last_program_name"] = current_program_name
                publish_new_program(current_program_name)
    
        # Increment track count
        state["tracks_played"] += 1
    
        # Log track info
        logging.info(f'Now Playing: {now_playing.artist} - {now_playing.title} '
                    f'[{formatted_datetime}]')
        logging.debug(f"{now_playing}")
    
        # Check for skip conditions
        if now_playing.artist in config.skip_artists:
            logging.info(f"Not publishing artist: {now_playing.artist}")
            return
        
        if now_playing.title in config.skip_titles:
            logging.info(f"Not publishing title: {now_playing.title}")
            return
        
        # Publish to social platforms
        social_publisher = SocialPublisher(db_handler, config)
        for service in [
            SocialService.LASTFM,
            SocialService.LISTENBRAINZ,
            SocialService.FACEBOOK,
            SocialService.BLUESKY,
            SocialService.SOUNDEXCHANGE
        ]:
            social_publisher.publish_socials(
                service,
                now_playing.artist,
                now_playing.title,
                now_playing.album,
                now_playing.publisher,
                now_playing.ISRC
            )
    
        # Process artwork and update web files
        source_dir = Path(config.script_home)
        playout_data.copy_album_artwork(source_dir, dest_dir, config)  # Pass config here
        playout_data.write_playlist_json(dest_dir, config)
        state["last_published_image"] = now_playing.publish_image
    
    except Exception as e:
        logging.error(f"Error processing new track data: {e}", exc_info=True)


def publish_new_program(program_name: str) -> None:
    """
    Publish information about a new program starting
    
    Args:
        program_name: Name of the new program
    """
    logging.info(f"Publishing new program: {program_name}")
    # Add additional program transition handling here

