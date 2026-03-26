from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# Engine — one connection pool for the whole app
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "development",  # logs SQL queries in dev mode
    pool_pre_ping=True,  # checks connection is alive before using it
)

# Session factory — used to create DB sessions
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Base class — all ORM models will inherit from this
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency function that provides a DB session.
    Always closes the session after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()