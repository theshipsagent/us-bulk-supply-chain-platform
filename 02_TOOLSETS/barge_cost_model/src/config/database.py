"""
Database connection and session management.
Uses SQLAlchemy for ORM and connection pooling.
"""

from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy base for ORM models
Base = declarative_base()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
)


# Enable PostGIS on connection
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Enable PostGIS extension on new connections."""
    with dbapi_conn.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC';")


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in standalone scripts.

    Usage:
        with get_db_session() as db:
            results = db.query(WaterwayLink).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def get_db_connection():
    """
    Get raw database connection for direct SQL execution.

    Usage:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT * FROM waterway_links"))
    """
    return engine.connect()


def init_db():
    """
    Initialize database tables.
    Note: Schema is created via schema.sql, this is for ORM models if needed.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


def verify_db_connection() -> bool:
    """
    Verify database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection verified")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def verify_postgis() -> bool:
    """
    Verify PostGIS extension is enabled.

    Returns:
        bool: True if PostGIS is available, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT PostGIS_version();")
            )
            version = result.fetchone()[0]
            logger.info(f"PostGIS version: {version}")
            return True
    except Exception as e:
        logger.error(f"PostGIS not available: {e}")
        return False


def get_table_counts() -> dict:
    """
    Get row counts for all main tables.
    Useful for verification after data loading.

    Returns:
        dict: Table name -> row count mapping
    """
    tables = [
        "waterway_links",
        "locks",
        "docks",
        "link_tonnages",
        "vessels",
        "computed_routes",
    ]

    counts = {}
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = result.fetchone()[0]

    return counts


if __name__ == "__main__":
    """
    Test database connection when run as script.

    Usage:
        python src/config/database.py
    """
    print("Testing database connection...")

    if verify_db_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        exit(1)

    if verify_postgis():
        print("✓ PostGIS extension enabled")
    else:
        print("✗ PostGIS extension not found")
        exit(1)

    print("\nTable row counts:")
    counts = get_table_counts()
    for table, count in counts.items():
        print(f"  {table}: {count:,}")

    print("\nDatabase check complete!")
