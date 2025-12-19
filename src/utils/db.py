from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from werkzeug.local import LocalProxy

from src.base.model import Base
from src.model import *
from src.utils.config import config

from .log import setup_logger

logger = setup_logger(__name__, "db.log")

# --- Setup ---
# 1. Use create_engine as normal
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
    """Drop all tables defined in the models."""
    with app.app_context():
        Base.metadata.drop_all(bind=engine)
