# src/services/base_service.py
"""
Base service interface for social media services
"""

from abc import ABC, abstractmethod
from models.track_info import TrackInfo

class SocialMediaService(ABC):
    @abstractmethod
    def publish(self, track: TrackInfo) -> bool:
        """
        Publish track information to a social media service
        
        Args:
            track: TrackInfo instance containing track details
            
        Returns:
            bool: True if publication succeeded, False otherwise
        """
        pass

