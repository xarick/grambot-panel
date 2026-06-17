from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.modules.templates.schemas import TemplateCreate, TemplateOut, TemplateUpdate
from app.modules.templates.service import create_template, delete_template, list_templates, update_template
from app.modules.users.models import User

router = APIRouter()


@router.get("", response_model=list[TemplateOut])
def get_templates(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return list_templates(db)


@router.post("", response_model=TemplateOut)
def add_template(body: TemplateCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_template(db, body.title, body.text, user.id)


@router.patch("/{template_id}", response_model=TemplateOut)
def edit_template(template_id: int, body: TemplateUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return update_template(db, template_id, body.title, body.text)


@router.delete("/{template_id}", status_code=204)
def remove_template(template_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    delete_template(db, template_id)
