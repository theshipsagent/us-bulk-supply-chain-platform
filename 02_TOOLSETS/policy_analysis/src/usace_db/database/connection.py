"""
Database connection management for USACE vessel database.
Uses DuckDB for fast, serverless analytics.
"""
import os
from pathlib import Path
import duckdb
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages DuckDB database connections."""

    def __init__(self, db_path=None):
        """
        Initialize database connection.

        Args:
            db_path: Path to DuckDB database file (default: data/usace_vessels.duckdb)
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / 'data' / 'usace_vessels.duckdb'

        self.db_path = Path(db_path)
        self.conn = None

        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        """Create database connection."""
        try:
            # Connect to DuckDB (creates file if doesn't exist)
            self.conn = duckdb.connect(str(self.db_path))

            # Configure for better performance with large datasets
            self.conn.execute("SET memory_limit='4GB'")
            self.conn.execute("SET threads TO 4")

            logger.info(f"Connected to DuckDB database: {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def execute_sql_file(self, sql_file_path):
        """
        Execute SQL from a file.

        Args:
            sql_file_path: Path to .sql file

        Returns:
            bool: Success status
        """
        try:
            if not self.conn:
                self.connect()

            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql = f.read()

            # Execute the entire SQL file
            # DuckDB can handle multiple statements
            self.conn.execute(sql)

            logger.info(f"Executed SQL file: {sql_file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to execute SQL file {sql_file_path}: {e}")
            return False

    def execute(self, sql, params=None):
        """
        Execute a SQL query.

        Args:
            sql: SQL query string
            params: Optional parameters for parameterized queries

        Returns:
            DuckDB result object
        """
        if not self.conn:
            self.connect()

        if params:
            return self.conn.execute(sql, params)
        else:
            return self.conn.execute(sql)

    def query(self, sql, params=None):
        """
        Execute a SQL query and return results as list of tuples.

        Args:
            sql: SQL query string
            params: Optional parameters

        Returns:
            List of result tuples
        """
        result = self.execute(sql, params)
        return result.fetchall()

    def query_df(self, sql, params=None):
        """
        Execute a SQL query and return results as pandas DataFrame.

        Args:
            sql: SQL query string
            params: Optional parameters

        Returns:
            pandas DataFrame
        """
        result = self.execute(sql, params)
        return result.df()

    @property
    def engine(self):
        """Compatibility property for SQLAlchemy-like access."""
        return self.conn

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
