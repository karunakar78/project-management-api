from sqlalchemy.orm import Session
from typing import Literal

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.exceptions import ProjectNotFoundError
from sqlalchemy.exc import SQLAlchemyError



def create_project(
    db: Session,
    project_data: ProjectCreate,
    owner_id: int
):
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=owner_id
    )

    try:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    except SQLAlchemyError:
        db.rollback()
        raise


def get_project(
    db: Session,
    project_id: int,
    owner_id: int
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == owner_id
        )
        .first()
    )

    if project is None:
        raise ProjectNotFoundError(
            f"Project {project_id} not found"
        )

    return project


def get_projects(
    db: Session,
    owner_id: int,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    sort_by: Literal["id", "name"] = "id"
):
    query = db.query(Project).filter(
        Project.owner_id == owner_id
    )

    if search:
        query = query.filter(
            Project.name.ilike(f"%{search}%")
        )

    sort_column = getattr(Project, sort_by)
    query = query.order_by(sort_column)

    return query.offset(skip).limit(limit).all()


def update_project(
    db: Session,
    project: Project,
    project_data: ProjectUpdate
):
    update_data = project_data.model_dump(exclude_unset=True)

    try:
        for field, value in update_data.items():
            setattr(project, field, value)

        db.commit()
        db.refresh(project)
        return project
    except SQLAlchemyError:
        db.rollback()
        raise


def delete_project(db: Session, project: Project):
    try:
        db.delete(project)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
