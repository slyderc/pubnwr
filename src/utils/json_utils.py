"""
JSON utility functions for PubNWR
"""

import re
import json
import logging
from typing import Optional, Any, Dict

def sanitize_json(content: str) -> str:
    """
    Sanitize JSON content to handle common issues in playout data
    
    Args:
        content: Raw JSON string from playout system
        
    Returns:
        str: Sanitized JSON string
    """
    def _fix_values(match):
        """Fix individual JSON value matches"""
        key = match.group(1)
        value = match.group(2).replace('\\', r'\\')  # Escape backslashes
        value = value.replace('"', r'\"')  # Escape quotes
        return f'"{key}": "{value}"'
    
    try:
        # Clean up common JSON issues
        content = re.sub(r'"([^"]+)": "([^"]+)"', _fix_values, content)
        content = re.sub(r'[\x00-\x1F\x7F]', '', content)  # Remove control chars
        content = re.sub(r',\s*}', '}', content)  # Remove trailing commas
        content = re.sub(r',\s*\]', ']', content)  # Remove trailing array commas
        return content
        
    except Exception as e:
        logging.error(f"Error sanitizing JSON: {e}")
        return content

def safe_json_loads(content: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON string with error handling
    
    Args:
        content: JSON string to parse
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON object or None on error
    """
    try:
        # First try direct parsing
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            # If that fails, try sanitizing first
            sanitized = sanitize_json(content)
            return json.loads(sanitized)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON even after sanitizing: {e}")
            return None
    except Exception as e:
        logging.error(f"Unexpected error parsing JSON: {e}")
        return None

def safe_json_dumps(obj: Any, 
                   indent: int = 4, 
                   ensure_ascii: bool = False) -> Optional[str]:
    """
    Safely convert object to JSON string with error handling
    
    Args:
        obj: Object to convert to JSON
        indent: Number of spaces for indentation
        ensure_ascii: Whether to escape non-ASCII characters
        
    Returns:
        Optional[str]: JSON string or None on error
    """
    try:
        return json.dumps(obj, 
                         indent=indent, 
                         ensure_ascii=ensure_ascii)
    except Exception as e:
        logging.error(f"Failed to convert object to JSON: {e}")
        return None

