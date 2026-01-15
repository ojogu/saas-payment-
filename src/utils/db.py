from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from werkzeug.local import LocalProxy

from src.base.model import Base
from src.model import *
from src.utils.config import config

from .log import setup_logger
from sqlalchemy import inspect

logger = setup_logger(__name__, "db.log")

# --- Setup ---
# 1. Use create_engine 
# engine = create_engine(config.TEST_DB)
engine = create_engine(config.PROD_DATABASE_URL)

# 2. Use the standard synchronous Session
# The 'sessionmaker' pattern is often used for thread safety in web apps
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 3. Use the session manager pattern to get a session
def _get_db():
    """Provides a session for the current request."""
    if "db" not in g:
        # Create a new session (Type: Session)
        g.db = SessionLocal()
    return g.db


db:Session = LocalProxy(_get_db)


def init_db(app: Flask):
    @app.before_request
    def setup_db():
        _get_db()


def close_db(app: Flask):
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Closes the session after the request is finished."""
        db:Session = g.pop("db", None)
        if db is not None:
            try:
                if exception:
                    db.rollback()
                db.close()
            except Exception as e:
                logger.error(f"Error during session cleanup: {e}")


def create_tables(app: Flask):
    """Create all tables defined in the models."""
    with app.app_context():
        Base.metadata.create_all(bind=engine)


def drop_tables(app: Flask):
    """
    Drop all tables in the database, ignoring foreign key constraints.

    This synchronous function uses the SQLAlchemy engine to drop all tables
    that are defined in the Base metadata. It disables foreign key checks
    during the drop operation to avoid constraint violations.

    Caution: This operation will delete all data in the tables. Use with care.
    """
    with app.app_context():
        with engine.begin() as conn:
            # Disable foreign key checks (database-specific)
            dialect_name = conn.dialect.name

            if dialect_name == 'postgresql':
                # PostgreSQL: Explicitly drop each table with CASCADE
                from sqlalchemy import text
                for table in reversed(Base.metadata.sorted_tables):
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table.name}" CASCADE'))

            elif dialect_name == 'mysql':
                # MySQL: Disable foreign key checks
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
                Base.metadata.drop_all(bind=engine)
                conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))

            elif dialect_name == 'sqlite':
                # SQLite: Disable foreign key enforcement
                conn.execute(text('PRAGMA foreign_keys = OFF'))
                Base.metadata.drop_all(bind=engine)
                conn.execute(text('PRAGMA foreign_keys = ON'))

            else:
                # Default fallback for other databases
                Base.metadata.drop_all(bind=engine)


# Assuming your db object is already created
# db = SQLAlchemy(app)

def debug_database():
    # 1. Get the current Database URI
    current_uri = engine.url
    print(f"--- Currently connected to: {current_uri} ---")

    # 2. Get the table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"--- Tables found: ({len(tables)}) ---")
    for table in tables:
        print(f"  - {table}")
