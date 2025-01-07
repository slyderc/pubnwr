"""
Track information data model for PubNWR
"""

import re
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrackInfo:
    artist: str
    title: str
    album: str
    publisher: str
    ISRC: str
    image: str
    publish_image: str
    start_time: str
    duration: int
    program_title: str
    presenter: str

    @classmethod
    def from_json(cls, data: dict) -> 'TrackInfo':
        """Create a TrackInfo instance from JSON data"""
        # Check if this is a valid song
        if not cls.is_valid_song(data):
            # Use empty strings but set default image
            return cls(
                artist="",
                title="",
                album="",
                publisher="",
                ISRC="",
                image="default-art.jpg",  # This will be overridden
                publish_image="default-art.jpg",  # No unique name for default
                start_time=datetime.utcnow().isoformat(),
                duration=0,
                program_title=data.get('program', 'Unknown Program').strip(),
                presenter=data.get('presenter', '').strip()
            )

        # Regular song processing
        publish_image = f"{uuid.uuid4().hex}.jpg"
        logging.debug(f"Generated new publish_image name: {publish_image}")
        
        return cls(
            artist=data.get('artist', 'Unknown Artist').strip(),
            title=cls._clean_title(data.get('title', 'Unknown Title')),
            album=data.get('album', 'Unknown Album').strip(),
            publisher=data.get('publisher', '').strip(),
            ISRC=data.get('ISRC', '').strip(),
            image=data.get('image', 'art-00.jpg').strip(),
            publish_image=publish_image,
            start_time=data.get('starttime', datetime.utcnow().isoformat()),
            duration=int(data.get('duration', 0)),
            program_title=data.get('program', 'Unknown Program').strip(),
            presenter=data.get('presenter', '').strip()
        )

    @staticmethod
    def _clean_title(title: str) -> str:
        """
        Clean the title by removing text after bracketed sections
        
        Args:
            title: Raw title string
            
        Returns:
            str: Cleaned title string
        """
        # Split on any of (, [, or < and take the first part
        cleaned = re.split(r'[\(\[\<]', title)[0]
        return cleaned.strip()

    @staticmethod
    def is_valid_song(data: dict) -> bool:
        """
        Check if the data represents a valid song
        
        Args:
            data: Dictionary containing track information
            
        Returns:
            bool: True if this appears to be a valid song
        """
        # Check for presence of required fields
        artist = data.get('artist', '').strip()
        title = data.get('title', '').strip()
        
        # Must have both artist and title
        return bool(artist and title)

    def __repr__(self):
        """String representation of TrackInfo"""
        return (
            f"TrackInfo(artist='{self.artist}', title='{self.title}', "
            f"album='{self.album}', publisher='{self.publisher}', "
            f"ISRC='{self.ISRC}', duration={self.duration})"
        )