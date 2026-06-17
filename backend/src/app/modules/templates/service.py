from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.templates import repository
from app.modules.templates.models import MessageTemplate


def list_templates(db: Session) -> list[MessageTemplate]:
    return repository.get_all(db)


def create_template(db: Session, title: str, text: str, created_by_id: int) -> MessageTemplate:
    return repository.create(db, title=title, text=text, created_by_id=created_by_id)


def update_template(
    db: Session, template_id: int, title: str | None, text: str | None
) -> MessageTemplate:
    template = repository.get_by_id(db, template_id)
    if not template:
        raise NotFoundError("Template not found")

    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if text is not None:
        kwargs["text"] = text

    if kwargs:
        template = repository.update(db, template, **kwargs)
    return template


def delete_template(db: Session, template_id: int) -> None:
    template = repository.get_by_id(db, template_id)
    if not template:
        raise NotFoundError("Template not found")
    repository.delete(db, template)
