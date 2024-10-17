import psycopg2
from psycopg2 import pool
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the connection pool globally
db_pool = None

def init_pool():
    global db_pool
    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            1,  # minconn
            10,  # maxconn
            dbname="virtual_assistant_database",
            user="postgres",
            password="Lg26y0M@x",
            host="91.147.92.32"
        )
        if db_pool:
            logger.info("Database connection pool created successfully.")
    except Exception as e:
        logger.error(f"Error creating connection pool: {e}")

def get_connection():
    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def release_connection(conn):
    try:
        db_pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error returning connection to pool: {e}")


def get_phone_number_from_db(user_id: int) -> str:
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT phone_number FROM users WHERE telegram_id = %s;", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return None
    finally:
        release_connection(conn)


def is_phone_number_in_whitelist(phone_number: str) -> bool:
    conn = get_connection()
    if not conn:
        return False
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM white_list WHERE phone_number = %s;", (phone_number,))
            return cursor.fetchone() is not None
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return False
    finally:
        release_connection(conn)


async def save_phone_to_db(user_id: int, phone_number: str) -> None:
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE users
                SET phone_number = %s
                WHERE telegram_id = %s;
            """, (phone_number, user_id))
        conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
    finally:
        release_connection(conn)


def save_user_to_db(user_id: int, username: str) -> None:
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO users (telegram_id, username)
                VALUES (%s, %s)
                ON CONFLICT (telegram_id) DO NOTHING;
            """
            cursor.execute(insert_query, (user_id, username))
        conn.commit()
    except psycopg2.Error as e:
        logger.error(f"Error saving user to the database: {e}")
    finally:
        release_connection(conn)


def decrement_message_limit(user_id: int) -> int:
    conn = get_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT limit_message FROM users WHERE telegram_id = %s;", (user_id,))
            result = cursor.fetchone()

            if not result or result[0] <= 0:
                return 0

            # Decrease the message limit by 1
            new_limit = result[0] - 1
            cursor.execute("UPDATE users SET limit_message = %s WHERE telegram_id = %s;", (new_limit, user_id))
            conn.commit()
            return new_limit
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return None
    finally:
        release_connection(conn)