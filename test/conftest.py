import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env.test', override=True)

from sqlalchemy import create_engine, text
from app.database import Base
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models import Items, Users
from fastapi.testclient import TestClient
import pytest
from passlib.context import CryptContext
from app.dependencies import get_current_user, get_db
from app.env_utils import get_required_env

SECRET_KEY = get_required_env('SECRET_KEY')
ALGORITHM = get_required_env('ALGORITHM')


SQLALCHEMY_DATABASE_URL = 'sqlite:///./testims.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})


TestingSessionLocal = sessionmaker(autocommit=False,autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user(role: str = 'admin'):
    return {'username':'Abzil', 'id':1, 'role': role}


client = TestClient(app)

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def as_role():
    def _set_role(role):
        app.dependency_overrides[get_current_user] = lambda: override_get_current_user(role)
    yield _set_role
    app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture
def test_item():
    item = Items(
        name = 'Cup',
        category = 'Tools',
        price = 1,
        quantity = 30
    )
    
    db = TestingSessionLocal()
    db.add(item)
    db.commit()
    yield db
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM items;"))
        connection.commit()


@pytest.fixture
def test_items_multiple():
    items = [
        Items(name='Hammer', category='Tools', price=15.0, quantity=10),
        Items(name='Chair', category='Furniture', price=50.0, quantity=0),
        Items(name='Laptop', category='Electronics', price=999.99, quantity=5),
    ]
    db = TestingSessionLocal()
    db.add_all(items)
    db.commit()
    yield items
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM items;"))
        connection.commit()


@pytest.fixture
def test_user():
    user = Users(
        username = 'Abzil',
        email = 'Abzil@gmail.com',
        first_name = 'Abzil',
        last_name = 'Rad',
        hash_password = bcrypt_context.hash('Abzil123'),
        is_active = True,
        role = 'admin',
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()


@pytest.fixture
def test_viewer_user():
    user = Users(
        username = 'viewer1',
        email = 'viewer1@gmail.com',
        first_name = 'viewer',
        last_name = 'viewer',
        hash_password = bcrypt_context.hash('viewer123'),
        is_active = True,
        role = 'viewer',
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()