"""
Main social media publishing coordinator
"""

import time
import json
import logging
import calendar
import requests
import urllib3
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

# Disable only the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from models.track_info import TrackInfo
from .lastfm_service import LastFMService
from .listenbrainz_service import ListenbrainzService
from .facebook_service import FacebookService
from .bluesky_service import BlueskyService
from .soundexchange_service import SoundExchangeService

class SocialService(Enum):
    """Enumeration of supported social media services"""
    LASTFM = "Last.FM"
    LISTENBRAINZ = "Listenbrainz"
    FACEBOOK = "Facebook"
    BLUESKY = "Bluesky"
    SOUNDEXCHANGE = "SoundExchange"

class SocialPublisher:
    def __init__(self, db_handler, config):
        """
        Initialize social publisher
        
        Args:
            db_handler: Database handler instance
            config: Configuration handler instance
        """
        self.db_handler = db_handler
        self.config = config
        self.do_publish_socials = config.do_publish_socials
        self.skip_titles = config.skip_titles
        self.skip_artists = config.skip_artists
        
        # Initialize services
        self.services: Dict[SocialService, SocialMediaService] = {
            SocialService.LASTFM: LastFMService(config.lastfm_auth),
            SocialService.LISTENBRAINZ: ListenbrainzService(config.lb_client),
            SocialService.FACEBOOK: FacebookService(config.fb_graph, config.fb_page_id),
            SocialService.BLUESKY: BlueskyService(config.bluesky),
            SocialService.SOUNDEXCHANGE: SoundExchangeService(db_handler)
        }

    def publish_socials(self, service: SocialService, artist: str, title: str,
                       album: str, publisher: str, ISRC: str) -> None:
        """
        Publish track information to a social media service
        
        Args:
            service: Social media service to publish to
            artist: Track artist
            title: Track title
            album: Album name
            publisher: Publisher/label name
            ISRC: International Standard Recording Code
        """

        """Publish track information to a social media service"""
        if not self.do_publish_socials:
            logging.info(f"SKIPPING - Not publishing to {service.value} as per configuration")
            return
        
        # Check if service is disabled in config
        disabled_services = json.loads(self.config.config.get("publish_exceptions", "disable_services", fallback="[]"))
        if service.value in disabled_services:
            logging.debug(f"SKIPPING - Service {service.value} is disabled in configuration")
            return

        # Check for previous publication
        if self._was_previously_published(service.value, artist, title):
            logging.debug(f"SKIPPING - Previously published this track for: {service.value}")
            return

        # Check skip lists
        if artist in self.skip_artists:
            logging.debug(f'Artist "{artist}" in skip list - not posting')
            return

        if title in self.skip_titles:
            logging.debug(f'Title "{title}" in skip list - not posting')
            return

        try:
            # Get current time and listener count
            utcnow = datetime.utcnow()
            publish_time = calendar.timegm(utcnow.utctimetuple())
            listeners = self._get_listeners_count()
            
            # Create track info object
            track_info = TrackInfo(
                artist=artist,
                title=title,
                album=album,
                publisher=publisher,
                ISRC=ISRC,
                image="",  # Not needed for social publishing
                publish_image="",
                start_time=utcnow.isoformat(),
                duration=0,  # Not needed for social publishing
                program_title="",
                presenter=""
            )

            # Publish to service
            if service in self.services:
                success = self.services[service].publish(track_info)
                if success:
                    self._record_published(service.value, artist, title, album,
                                         publisher, ISRC, listeners, publish_time)
            else:
                logging.warning(f"Unknown service: {service.value}")
    
        except Exception as error:
            logging.error(f"Failed to publish to {service.value}: {error}")

    def _was_previously_published(self, service: str, artist: str, title: str) -> bool:
        """
        Check if track was previously published to service
        
        Args:
            service: Name of the service
            artist: Track artist
            title: Track title
            
        Returns:
            bool: True if track was previously published
        """
        sql_query = ("SELECT artist, title FROM realtime "
                    "WHERE service = ? AND artist = ? AND title = ?")
        try:
            results = self.db_handler.execute_query(sql_query, (service, artist, title))
            return bool(results and len(results) > 0)
        except Exception as error:
            logging.error(f"Error checking previous publication: {error}")
            return False
    
    def _get_listeners_count(self) -> int:
        """
        Get current listener count from Azuracast
        
        Returns:
            int: Number of current listeners
        """
        try:
            response = requests.get(
                url=self.config.azcast_url,
                verify=False,
                timeout=5
            )
            response.raise_for_status()
            return (response.json()
                   .get('station', {})
                   .get('mounts', [{}])[0]
                   .get('listeners', {})
                   .get('total', 0))
        except Exception as e:
            logging.error(f"Failed to fetch listener count: {e}")
            return 0
        
    def _record_published(self, service: str, artist: str, title: str,
                         album: str, publisher: str, ISRC: str,
                         listeners: int, timestamp: int) -> None:
        """
        Record successful publication to database
        
        Args:
            service: Name of the service
            artist: Track artist
            title: Track title
            album: Album name
            publisher: Publisher/label name
            ISRC: International Standard Recording Code
            listeners: Number of listeners at time of publication
            timestamp: Unix timestamp of publication
        """
        sql_insert = ("INSERT INTO realtime(service, artist, title, timestamp) "
                     "VALUES (?,?,?,?)")
        sql_delete = "DELETE FROM realtime WHERE service=?"
        
        try:
            self.db_handler.execute_non_query(sql_delete, (service,))
            self.db_handler.execute_non_query(
                sql_insert, 
                (service, artist, title, timestamp)
            )
        except Exception as error:
            logging.error(f"Failed to record publication: {error}")

