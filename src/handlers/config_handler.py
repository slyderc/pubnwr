"""
Configuration handler for PubNWR
Manages all configuration loading and access
"""

import json
import logging
from pathlib import Path
from configparser import ConfigParser
from typing import Dict, List

import pylast
import pylistenbrainz
import facebook
from atproto import Client

class ConfigHandler:
    def __init__(self, config_file: str):
        """
        Initialize configuration handler
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = ConfigParser()
        self._load_config()

    def _load_config(self) -> None:
        """Load all configuration settings from file"""
        self.config.read(self.config_file)
        
        # Load configurations in order
        self._setup_logging()
        self._load_paths()
        self._load_timing()
        self._load_social_configs()
        self._load_exceptions()
        self._load_advanced_settings()  # Add this line
        
        logging.info(f'Configuration loaded: {self.config_file} - DEBUG: {self.debug_log}')

    def _setup_logging(self) -> None:
        """Configure logging based on settings"""
        self.debug_log = self.config.getboolean('main', 'debug_log', fallback=False)
        self.verbose_log = self.config.getboolean('main', 'verbose_log', fallback=False)
        self.logfile = self.config.get('main', 'logfile', 
                                     fallback='/var/log/pubnwr_Myriad.log')
        
        log_level = (logging.DEBUG if self.debug_log else 
                    logging.INFO if self.verbose_log else 
                    logging.WARNING)
        
        logging.basicConfig(
            filename=self.logfile,
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )

    def _load_paths(self):
        """Load all path configurations"""
        self.script_home = self.config.get('main', 'script_home')
        self.db_file = self.config.get('main', 'db_file')
        
        # Handle default_img relative to script_home if not absolute
        default_img = self.config.get('main', 'default_img')
        if not Path(default_img).is_absolute():
            self.default_img = str(Path(self.script_home) / default_img)
        else:
            self.default_img = default_img
            
        self.host_url = self.config.get('main', 'host_url')
        self.azcast_url = self.config.get('main', 'azcast_url')
        self.root_publish_path = self.config.get('main', 'root_publish_path')
        self.playout_file = self.config.get('main', 'playout_file')
        self.url_publish_dir = self.config.get('main', 'url_publish_dir')
        
        # Derived paths
        self.pub_json_file = str(Path(self.script_home) / self.playout_file)
        self.web_json_file = str(Path(self.root_publish_path) / self.playout_file)
        self.now_playing_file = str(Path(self.root_publish_path) / 'nowplaying.txt')
        self.playout_artfile = str(Path(self.script_home) / 'art-00.jpg')

    def _load_timing(self) -> None:
        """Load timing-related configurations"""
        self.offset_adjust = int(self.config.get('main', 'offset_adjust'))
        self.timezone = self.config.get('main', 'timezone')
        self.event_timeout = int(self.config.get('main', 'event_timeout', 
                                               fallback=300))

    def _load_social_configs(self) -> None:
        """Load social media service configurations"""
        self._setup_lastfm()
        self._setup_listenbrainz()
        self._setup_facebook()
        self._setup_bluesky()

    def _setup_lastfm(self) -> None:
        """Configure Last.FM authentication"""
        self.lastfm_auth = pylast.LastFMNetwork(
            api_key=self.config.get('lastfm_auth', 'api_key'),
            api_secret=self.config.get('lastfm_auth', 'api_secret'),
            username=self.config.get('lastfm_auth', 'username'),
            password_hash=self.config.get('lastfm_auth', 'password')
        )

    def _setup_listenbrainz(self) -> None:
        """Configure Listenbrainz authentication"""
        self.listenbrainz_auth = self.config.get('listenbrainz_auth', 'auth_token')
        self.lb_client = pylistenbrainz.ListenBrainz()
        self.lb_client.set_auth_token(self.listenbrainz_auth)

    def _setup_facebook(self) -> None:
        """Configure Facebook authentication"""
        self.fb_access_token = self.config.get('facebook_auth', 'access_token')
        self.fb_page_id = self.config.get('facebook_auth', 'page_id')
        self.fb_app_id = self.config.get('facebook_auth', 'app_id')
        self.fb_app_secret = self.config.get('facebook_auth', 'app_secret')
        self.fb_graph = facebook.GraphAPI(access_token=self.fb_access_token)

    def _setup_bluesky(self) -> None:
        """Configure Bluesky authentication"""
        self.bsky_username = self.config.get('bluesky_auth', 'bsky_username')
        self.bsky_password = self.config.get('bluesky_auth', 'bsky_password')
        self.bluesky = Client()
        self.bluesky.login(self.bsky_username, self.bsky_password)

    def _load_exceptions(self) -> None:
        """Load publishing exceptions and skip lists"""
        self.do_publish_socials = self.config.getboolean(
            'publish_exceptions', 
            'do_publish_socials', 
            fallback=False
        )
        self.skip_artists = json.loads(
            self.config.get('publish_exceptions', 'skip_artists')
        )
        self.skip_titles = json.loads(
            self.config.get('publish_exceptions', 'skip_titles')
        )

    def reload(self) -> None:
        """Reload all configuration settings"""
        self._load_config()

    def _load_advanced_settings(self):
        """Load advanced monitoring settings"""
        advanced = self.config['advanced']
        
        # File monitoring settings
        self.min_file_size = advanced.getint('min_file_size', 50)
        self.debounce_time = advanced.getfloat('debounce_time', 2.0)
        self.stability_checks = advanced.getint('stability_checks', 3)
        self.max_wait_time = advanced.getfloat('max_wait_time', 10.0)
        
        # Retry settings
        self.max_retries = advanced.getint('max_retries', 3)
        self.retry_delay = advanced.getfloat('retry_delay', 1.0)
        
        # Network timeouts
        self.connect_timeout = advanced.getint('connect_timeout', 5)
        self.read_timeout = advanced.getint('read_timeout', 10)

