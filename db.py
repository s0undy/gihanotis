"""
Database connection and query helpers for GiHaNotis
Provides connection management and query execution utilities
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
import logging
from contextlib import contextmanager

# Global connection pool
_connection_pool = None

# Logger
logger = logging.getLogger(__name__)


def init_connection_pool(minconn=1, maxconn=10):
    """
    Initialize the database connection pool.
    Should be called once at application startup.
    """
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'gihanotis'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                cursor_factory=RealDictCursor
            )
            logger.info(f"Database connection pool initialized: min={minconn}, max={maxconn}")
        except psycopg2.Error as e:
            logger.error(f"Database connection pool error: {e}", exc_info=True)
            raise


def get_db_connection():
    """
    Get a connection from the pool.
    Uses RealDictCursor to return results as dictionaries.
    """
    global _connection_pool
    if _connection_pool is None:
        init_connection_pool()

    try:
        conn = _connection_pool.getconn()
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}", exc_info=True)
        raise


def return_connection(conn):
    """
    Return a connection to the pool.
    """
    global _connection_pool
    if _connection_pool is not None and conn is not None:
        _connection_pool.putconn(conn)


@contextmanager
def get_db_cursor():
    """
    Context manager for database operations.
    Automatically handles connection and cursor cleanup.
    Returns connection to pool when done.

    Usage:
        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM requests")
            results = cur.fetchall()
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}", exc_info=True)
        raise
    finally:
        cur.close()
        return_connection(conn)


def execute_query(query, params=None, fetch=True):
    """
    Execute a SQL query and return results.

    Args:
        query (str): SQL query with %s placeholders for parameters
        params (tuple): Parameters to substitute in query
        fetch (bool): If True, return query results; if False, return rowcount

    Returns:
        list: Query results as list of dictionaries (if fetch=True)
        int: Number of affected rows (if fetch=False)

    Usage:
        # Fetch results
        results = execute_query("SELECT * FROM requests WHERE id = %s", (1,))

        # Insert/Update
        execute_query("INSERT INTO requests (...) VALUES (%s, %s)", (val1, val2), fetch=False)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        if fetch:
            result = cur.fetchall()
        else:
            conn.commit()
            result = cur.rowcount
        return result
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Query execution error: {e}", exc_info=True)
        raise
    finally:
        cur.close()
        return_connection(conn)


def execute_query_one(query, params=None):
    """
    Execute a SQL query and return a single result.

    Args:
        query (str): SQL query with %s placeholders
        params (tuple): Parameters to substitute in query

    Returns:
        dict: Single result as dictionary, or None if no results
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        result = cur.fetchone()
        conn.commit()  # Commit the transaction (needed for INSERT/UPDATE/DELETE with RETURNING)
        return result
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Query execution error: {e}", exc_info=True)
        raise
    finally:
        cur.close()
        return_connection(conn)
