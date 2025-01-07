"""
Listenbrainz implementation of social media service
"""

import time
import logging
import pylistenbrainz
from typing import Optional

from .base_service import SocialMediaService
from models.track_info import TrackInfo

class ListenbrainzService(SocialMediaService):
    def __init__(self, client: pylistenbrainz.ListenBrainz):
        """
        Initialize Listenbrainz service
        
        Args:
            client: Authenticated ListenBrainz client
        """
        self.client = client
    
    def publish(self, track: TrackInfo) -> bool:
        """
        Publish track to Listenbrainz
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if submission succeeded, False otherwise
        """
        try:
            # Create listen object
            lb_listen = pylistenbrainz.Listen(
                track_name=track.title,
                artist_name=track.artist,
                release_name=track.album,
                listened_at=int(time.time())
            )
            
            # Submit the listen
            self.client.submit_single_listen(lb_listen)
            
            logging.info(f"Published to Listenbrainz: {track.artist} - {track.title}")
            return True
            
        except Exception as e:
            logging.error(f"Listenbrainz publication failed: {e}")
            return False


