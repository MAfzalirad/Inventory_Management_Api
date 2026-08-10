from app.database import Base
from sqlalchemy import Column, Integer, String, Float,Boolean, ForeignKey


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hash_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String)


class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    price = Column(Float)
    quantity = Column(Integer)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))