"""
Facebook implementation of social media service
"""

import logging
import facebook
from typing import Optional

from .base_service import SocialMediaService
from models.track_info import TrackInfo

class FacebookService(SocialMediaService):
    def __init__(self, graph: facebook.GraphAPI, page_id: str):
        """
        Initialize Facebook service
        
        Args:
            graph: Authenticated Facebook GraphAPI instance
            page_id: Facebook page ID for posting
        """
        self.graph = graph
        self.page_id = page_id
    
    def publish(self, track: TrackInfo) -> bool:
        """
        Publish track to Facebook
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if post succeeded, False otherwise
        """
        try:
            # Create post message
            message = (f"Now Playing on Now Wave Radio:\n"
                      f"{track.artist} - {track.title}\n"
                      f"From the album: {track.album}")
            
            # Post to Facebook page
            self.graph.put_object(
                parent_object=self.page_id,
                connection_name="feed",
                message=message
            )
            
            logging.info(f"Published to Facebook: {track.artist} - {track.title}")
            return True
            
        except Exception as e:
            logging.error(f"Facebook publication failed: {e}")
            return False

