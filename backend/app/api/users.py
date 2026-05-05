from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/agents", response_model=list[UserRead])
def list_agents(_: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).where(User.role.in_([UserRole.admin, UserRole.agent])).order_by(User.full_name)))

