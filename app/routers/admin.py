from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from pydantic import Field
from starlette import status
from app.models import Items, Users
from app.dependencies import db_dependency, require_role, user_dependency, bcrypt_context
from typing_extensions import Annotated
from app.schemas import UserCreate, UserResponse, RoleEnum
from sqlalchemy.exc import IntegrityError
from typing import List

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


@router.get('/users', status_code=status.HTTP_200_OK, response_model=List[UserResponse])
async def get_all_users(db: db_dependency, user: user_dependency, role_check: Annotated[dict, Depends(require_role('admin'))]):
    users = db.query(Users).all()
    return users


@router.get('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserResponse)
async def get_user_by_id(db: db_dependency, user: user_dependency, user_id: Annotated[int, Path(gt=0)], role_check: Annotated[dict, Depends(require_role('admin'))]):
    requested_user = db.query(Users).filter(Users.id == user_id).first()
    if requested_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return requested_user


@router.put('/users/{user_id}/role', status_code=status.HTTP_204_NO_CONTENT)
async def change_user_role(db: db_dependency, user: user_dependency, user_id: Annotated[int, Path(gt=0)], new_role: Annotated[RoleEnum, Body(embed=True)], role_check: Annotated[dict, Depends(require_role('admin'))]):
    requested_user = db.query(Users).filter(Users.id == user_id).first()
    if requested_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    requested_user.role = new_role.value
    db.add(requested_user)
    db.commit()


@router.put('/users/{user_id}/deactivate', status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(db: db_dependency, user: user_dependency, user_id: Annotated[int, Path(gt=0)], role_check: Annotated[dict, Depends(require_role('admin'))]):
    requested_user = db.query(Users).filter(Users.id == user_id).first()
    if requested_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    # Block self-deactivation so an admin can't accidentally lock themselves
    # out of the system with no other admin able to reverse it.
    if requested_user.id == user.get('id'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot deactivate your own account')
    requested_user.is_active = False
    db.add(requested_user)
    db.commit()


@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: db_dependency, user: user_dependency, user_id: Annotated[int, Path(gt=0)], role_check: Annotated[dict, Depends(require_role('admin'))]):
    requested_user = db.query(Users).filter(Users.id == user_id).first()
    if requested_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    # Same rationale as deactivate: prevent an admin from deleting their own
    # account and potentially leaving the system with no admin left.
    if requested_user.id == user.get('id'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot delete your own account')
    db.delete(requested_user)
    db.commit()


@router.post('/create-user', status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(db: db_dependency, user_request: UserCreate, role_check: Annotated[dict, Depends(require_role('admin'))]):
    user_model = Users(
        username = user_request.username,
        email = user_request.email,
        first_name = user_request.first_name,
        last_name = user_request.last_name,
        hash_password = bcrypt_context.hash(user_request.password),
        is_active = True,
        role = user_request.role
    )
    try:
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Username or email already exists')
    return user_model