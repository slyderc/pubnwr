"""
Bluesky implementation of social media service
"""

import logging
from atproto import Client
from typing import Optional

from .base_service import SocialMediaService
from models.track_info import TrackInfo

class BlueskyService(SocialMediaService):
    def __init__(self, client: Client):
        """
        Initialize Bluesky service
        
        Args:
            client: Authenticated Bluesky client
        """
        self.client = client
    
    def publish(self, track: TrackInfo) -> bool:
        """
        Publish track to Bluesky
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if post succeeded, False otherwise
        """
        try:
            # Create post message
            message = (f"🎵 Now Playing on Now Wave Radio:\n"
                      f"{track.artist} - {track.title}\n"
                      f"From the album: {track.album}")
            
            # Post to Bluesky
            self.client.send_post(message)
            
            logging.info(f"Published to Bluesky: {track.artist} - {track.title}")
            return True
            
        except Exception as e:
            logging.error(f"Bluesky publication failed: {e}")
            return False

