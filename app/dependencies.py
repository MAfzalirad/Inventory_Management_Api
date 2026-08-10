from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from typing_extensions import Annotated
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from app.models import Users
from app.env_utils import get_required_env

SECRET_KEY = get_required_env('SECRET_KEY')
ALGORITHM = get_required_env('ALGORITHM')


auth2bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


async def get_current_user(token: Annotated[str, Depends(auth2bearer)], db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('username')
        user_id: int = payload.get('id')
        user_role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
        user_model = db.query(Users).filter(Users.id == user_id).first()
        if user_model is None or not user_model.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')


user_dependency = Annotated[dict, Depends(get_current_user)]


def require_role(*roles):
    """Build a FastAPI dependency that only allows the given roles through.

    This is a dependency *factory*, not a dependency itself: calling
    require_role('admin', 'manager') returns role_dependency, which is what
    actually gets passed to Depends() in a route signature, e.g.:

        role_check: Annotated[dict, Depends(require_role('admin'))]

    The factory pattern is needed because Depends() expects a callable with
    no args of its own (aside from its own sub-dependencies) — this is how
    we parameterize "which roles are allowed" per-route while still fitting
    FastAPI's dependency injection shape.
    """
    def role_dependency(user: user_dependency):
        if user.get('role') not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User does not have the required role.')
        return user
    return role_dependency