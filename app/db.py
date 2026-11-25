"""Database layer: SQLAlchemy models + engine.

SQLite locally (zero setup), PostgreSQL when DATABASE_URL points at one
(see schema.sql / docker-compose.yml). The model is identical on both.
"""

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

Base = declarative_base()


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (UniqueConstraint("country", "date", name="uq_country_date"),)

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    country = Column(String(100), nullable=False)
    confirmed = Column(BigInteger, nullable=False, default=0)
    recovered = Column(BigInteger, nullable=False, default=0)
    deaths = Column(BigInteger, nullable=False, default=0)
    new_confirmed = Column(BigInteger, nullable=False, default=0)
    new_deaths = Column(BigInteger, nullable=False, default=0)


def make_engine(url: str = DATABASE_URL):
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine)


def init_db(url: str = DATABASE_URL):
    """Create tables if they do not exist. Safe to call on every start."""
    eng = make_engine(url) if url != DATABASE_URL else engine
    Base.metadata.create_all(eng)
    return eng
