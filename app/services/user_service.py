from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.security import hash_password



from sqlalchemy.exc import SQLAlchemyError

def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise



def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()
