"""
Enhanced file handler for PubNWR with FTP-aware monitoring
"""

import time
import logging
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass
from hashlib import md5
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

@dataclass
class FileState:
    """Tracks the state of a monitored file"""
    size: int
    modification_time: float
    checksum: str
    last_processed: float
    content: Optional[str] = None


class FTPAwareFileHandler(FileSystemEventHandler):
    """
    File handler specifically designed for FTP file monitoring scenarios.
    Handles partial transfers, renames, and rapid file operations.
    """
    def __init__(
        self,
        file_path: Path,
        callback: Callable,
        config,
        min_file_size: int = 50
    ):
        """
        Initialize file handler
        
        Args:
            file_path: Path to the file to monitor
            callback: Function to call when file changes
            config: Application configuration instance
            min_file_size: Minimum expected file size in bytes
        """
        self.file_path = file_path
        self.callback = callback
        self.config = config
        self.min_file_size = min_file_size
        self.current_state: Optional[FileState] = None
        self.last_event_time = 0.0
        self.processing_lock = False

    def on_any_event(self, event) -> None:
        """Handle any file system event"""
        if event.src_path != str(self.file_path):
            return

        if event.event_type not in ("created", "modified"):
            logging.debug(f"Ignored event type '{event.event_type}' "
                        f"for file: {event.src_path}")
            return

        current_time = time.time()
        if current_time - self.last_event_time < self.config.debounce_time:
            logging.debug(f"Ignored event due to debounce: {event.src_path}")
            return
    
        if self.processing_lock:
            logging.debug("Skipping event - processing already in progress")
            return

        try:
            self.processing_lock = True
            self._handle_file_event(current_time)
        finally:
            self.processing_lock = False

    def _handle_file_event(self, current_time: float) -> None:
        """Process a file event with stability checks"""
        file_state = self._wait_for_file_stability()
        if not file_state:
            logging.warning("File did not stabilize within expected timeframe")
            return

        if not self._validate_file_state(file_state):
            logging.warning("File validation failed")
            return

        if self._is_duplicate_state(file_state):
            logging.debug("Skipping duplicate file state")
            return

        try:
            self._process_file(file_state)
        except Exception as e:
            logging.error(f"Error processing file: {e}")

    def _wait_for_file_stability(self) -> Optional[FileState]:
        """Wait for file to stabilize after FTP operations"""
        start_time = time.time()
        previous_state = None
        stable_count = 0

        while (time.time() - start_time) < self.config.max_wait_time:
            try:
                current_state = self._get_file_state()
                
                if not current_state:
                    stable_count = 0
                    time.sleep(0.5)
                    continue

                if previous_state and self._states_match(previous_state, current_state):
                    stable_count += 1
                    if stable_count >= self.config.stability_checks:
                        return current_state
                else:
                    stable_count = 0

                previous_state = current_state
                time.sleep(0.5)

            except Exception as e:
                logging.debug(f"Error checking file stability: {e}")
                stable_count = 0
                time.sleep(0.5)

        return None

    def _get_file_state(self) -> Optional[FileState]:
        """Get current file state with content hash"""
        try:
            if not self.file_path.exists():
                return None

            stats = self.file_path.stat()
            
            if stats.st_size < self.min_file_size:
                return None

            try:
                content = self.file_path.read_text(encoding='utf-8-sig')
                checksum = md5(content.encode()).hexdigest()
            except Exception as e:
                logging.debug(f"Error reading file: {e}")
                return None

            return FileState(
                size=stats.st_size,
                modification_time=stats.st_mtime,
                checksum=checksum,
                last_processed=time.time(),
                content=content
            )

        except Exception as e:
            logging.debug(f"Error getting file state: {e}")
            return None

    def _validate_file_state(self, state: FileState) -> bool:
        """Validate file state meets requirements"""
        if state.size < self.min_file_size:
            logging.warning(f"File too small: {state.size} bytes")
            return False

        try:
            # Basic JSON validation
            if not state.content.strip().startswith('{'):
                logging.warning("Content does not appear to be JSON")
                return False
        except Exception as e:
            logging.warning(f"Content validation failed: {e}")
            return False

        return True

    def _states_match(self, state1: FileState, state2: FileState) -> bool:
        """Compare two file states for equality"""
        return (
            state1.size == state2.size and
            state1.checksum == state2.checksum
        )

    def _is_duplicate_state(self, new_state: FileState) -> bool:
        """Check if this file state has already been processed"""
        if not self.current_state:
            return False

        time_diff = new_state.last_processed - self.current_state.last_processed
        
        return (self._states_match(new_state, self.current_state) and 
                time_diff < self.config.debounce_time)

    def _process_file(self, state: FileState) -> None:
        """Process the stabilized file"""
        try:
            self.callback(state.content)
            self.current_state = state
            logging.info(f"Successfully processed file update")
        except Exception as e:
            logging.error(f"Error in callback processing: {e}")
            raise


def start_file_watch(playout_file_path: Path, 
                    reload_callback: Callable, 
                    state: dict,
                    config) -> None:
    """Start monitoring a file for changes"""
    event_handler = FTPAwareFileHandler(
        file_path=playout_file_path,
        callback=reload_callback,
        config=config
    )
    
    observer = PollingObserver()
    observer.schedule(
        event_handler,
        path=str(playout_file_path.parent),
        recursive=False
    )

    try:
        observer.start()
        while True:
            time.sleep(1)
            current_time = time.time()
            next_check_time = (state["last_processed_time"] + 
                             state["current_track_duration"] + 
                             config.event_timeout)
            
            if current_time > next_check_time:
                logging.info("Forcing periodic check due to timeout...")
                try:
                    reload_callback()
                except Exception as e:
                    logging.error(f"Error during forced periodic check: {e}")
                finally:
                    state["last_processed_time"] = current_time

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Stopping observer...")
        observer.stop()
    finally:
        observer.join()

