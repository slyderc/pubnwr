"""
Database handler for PubNWR
Manages all database operations and connections
"""

import sqlite3
import logging
from typing import Optional, List, Tuple, Any

class DatabaseHandler:
    def __init__(self, db_path: str):
        """
        Initialize database handler
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Create a new SQLite connection for the current operation
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, 
                     query: str, 
                     params: Optional[Tuple[Any, ...]] = None) -> Optional[List[Tuple]]:
        """
        Execute a query with optional parameters and return the results
        
        Args:
            query: The SQL query to execute
            params: Optional parameters for the SQL query
            
        Returns:
            Optional[List[Tuple]]: Fetched rows from the database, or None if an error occurs
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.fetchall()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            return None
    
    def execute_non_query(self, 
                         query: str, 
                         params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Execute a query that does not return any results (e.g., INSERT, UPDATE, DELETE)
        
        Args:
            query: The SQL query to execute
            params: Optional parameters for the SQL query
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")

