from sqlalchemy.orm import Session

from app.modules.templates.models import MessageTemplate


def get_all(db: Session) -> list[MessageTemplate]:
    return db.query(MessageTemplate).order_by(MessageTemplate.created_at.desc()).all()


def get_by_id(db: Session, template_id: int) -> MessageTemplate | None:
    return db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()


def create(db: Session, title: str, text: str, created_by_id: int) -> MessageTemplate:
    template = MessageTemplate(title=title, text=text, created_by_id=created_by_id)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def update(db: Session, template: MessageTemplate, **kwargs) -> MessageTemplate:
    for key, value in kwargs.items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


def delete(db: Session, template: MessageTemplate) -> None:
    db.delete(template)
    db.commit()
