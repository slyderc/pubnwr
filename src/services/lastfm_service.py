"""
Last.FM implementation of social media service
"""

import time
import logging
import pylast
from typing import Optional

from .base_service import SocialMediaService
from models.track_info import TrackInfo

class LastFMService(SocialMediaService):
    def __init__(self, auth: pylast.LastFMNetwork):
        """
        Initialize Last.FM service
        
        Args:
            auth: Authenticated LastFMNetwork instance
        """
        self.auth = auth
        
    def publish(self, track: TrackInfo) -> bool:
        """
        Publish track to Last.FM
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if scrobble succeeded, False otherwise
        """
        try:
            # Scrobble the track
            self.auth.scrobble(
                artist=track.artist,
                title=track.title,
                timestamp=int(time.time()),
                album=track.album
            )
            
            logging.info(f"Published to Last.FM: {track.artist} - {track.title}")
            return True
            
        except Exception as e:
            logging.error(f"Last.FM publication failed: {e}")
            return False
    
    def get_now_playing(self, track: TrackInfo) -> bool:
        """
        Update Now Playing status on Last.FM
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if update succeeded, False otherwise
        """
        try:
            self.auth.update_now_playing(
                artist=track.artist,
                title=track.title,
                album=track.album,
                duration=track.duration
            )
            return True
        except Exception as e:
            logging.error(f"Last.FM now playing update failed: {e}")
            return False
