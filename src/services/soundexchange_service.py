"""
SoundExchange reporting service
"""

import time
import logging
from typing import Optional

from .base_service import SocialMediaService
from models.track_info import TrackInfo

class SoundExchangeService(SocialMediaService):
    def __init__(self, db_handler):
        """
        Initialize SoundExchange service
        
        Args:
            db_handler: Database handler for recording plays
        """
        self.db_handler = db_handler
    
    def publish(self, track: TrackInfo) -> bool:
        """
        Record track play for SoundExchange reporting
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if recording succeeded, False otherwise
        """
        try:
            logging.info(f"Recording play for SoundExchange: "
                        f"{track.artist} - {track.title} [{track.album}]")
                        
            sql_insert = (
                "INSERT INTO soundexchange("
                "featured_artist, sound_recording_title, ISRC, album_title, "
                "marketing_label, actual_total_performances, timestamp"
                ") VALUES (?,?,?,?,?,?,?)"
            )
            
            self.db_handler.execute_non_query(
                sql_insert,
                (track.artist, track.title, track.ISRC, track.album,
                 track.publisher, 1, int(time.time()))
            )
            return True
            
        except Exception as e:
            logging.error(f"SoundExchange recording failed: {e}")
            return False

