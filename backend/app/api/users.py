from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreateByAdmin, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/agents", response_model=list[UserRead])
def list_agents(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.role.in_([UserRole.admin, UserRole.agent]), User.is_active.is_(True))
            .order_by(User.full_name)
        )
    )


def get_user_or_404(user_id: int, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def active_admin_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.role == UserRole.admin, User.is_active.is_(True))) or 0


def ensure_admin_not_locked_out(target_user: User, current_user: User, payload: UserUpdate, db: Session) -> None:
    if target_user.id == current_user.id:
        if payload.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot deactivate yourself")
        if payload.role is not None and payload.role != UserRole.admin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot remove your own admin role")

    removes_active_admin = (
        target_user.role == UserRole.admin
        and target_user.is_active
        and ((payload.role is not None and payload.role != UserRole.admin) or payload.is_active is False)
    )
    if removes_active_admin and active_admin_count(db) <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one active admin must remain")


@router.get("", response_model=list[UserRead])
def list_users(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())))


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateByAdmin, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name or payload.email.split("@")[0],
        role=payload.role,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_or_404(user_id, db)
    ensure_admin_not_locked_out(user, current_user, payload, db)

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserRead)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = get_user_or_404(user_id, db)
    payload = UserUpdate(is_active=False)
    ensure_admin_not_locked_out(user, current_user, payload, db)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
