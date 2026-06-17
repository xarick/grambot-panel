from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core import config
from app.core.security import create_access_token
from app.db.session import get_db
from app.modules.users.schemas import LoginRequest, ProfileUpdate, UserOut
from app.modules.users.service import authenticate, update_profile
from app.api.v1.deps import get_current_user
from app.modules.users.models import User

router = APIRouter()

COOKIE_NAME = "access_token"


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, body.username, body.password)
    token = create_access_token(user.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=not config.DEBUG,
        max_age=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        COOKIE_NAME,
        httponly=True,
        samesite="lax",
        secure=not config.DEBUG,
    )
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    body: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return update_profile(db, user, body.username, body.current_password, body.new_password)


@router.get("/login-path")
def login_path():
    return {"path": config.ADMIN_LOGIN_PATH}
