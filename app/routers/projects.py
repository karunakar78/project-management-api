from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Literal

from app.database import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import project_service
from app.models.user import User
from app.security import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])



@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return project_service.create_project(
            db,
            project_data,
            owner_id=current_user.id
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create project"
        )



@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    search: str | None = Query(default=None),
    sort_by: Literal["id", "name"] = Query(default="id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.get_projects(
        db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search,
        sort_by=sort_by
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return project_service.get_project(
        db,
        project_id,
        owner_id=current_user.id
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = project_service.get_project(
        db,
        project_id,
        owner_id=current_user.id
    )

    try:
        return project_service.update_project(
            db, project, project_data
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to update project"
        )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = project_service.get_project(
        db,
        project_id,
        owner_id=current_user.id
    )

    try:
        project_service.delete_project(db, project)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete project"
        )