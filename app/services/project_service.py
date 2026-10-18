from sqlalchemy.orm import Session

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.exceptions import ProjectNotFoundError
from sqlalchemy.exc import SQLAlchemyError


def create_project(db: Session, project_data: ProjectCreate):
    project = Project(
        name=project_data.name,
        description=project_data.description
    )

    try:
        db.add(project)
        db.commit()
        db.refresh(project)
        return project
    except SQLAlchemyError:
        db.rollback()
        raise


def get_project(db: Session, project_id: int):
    project = db.get(Project, project_id)

    if project is None:
        raise ProjectNotFoundError("Project not found")

    return project


def get_projects(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Project).offset(skip).limit(limit).all()


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
