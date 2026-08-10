from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.env_utils import get_required_env


SQLALCHEMY_DATABASE_URL = get_required_env("DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()