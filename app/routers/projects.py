from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectResponse])
def get_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    projects = db.query(Project).offset(skip).limit(limit).all()

    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    for project in projects:
        if project["id"] == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):
    new_project = Project(
        name=project.name,
        description=project.description
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.patch("/{project_id}", response_model=ProjectResponse)
def project_update(project_id: int, project_update: ProjectUpdate):
    for project in projects:
        if project["id"] == project_id:
            if project_update["name"] is not None:
                project["name"] = project_update["name"]

            if project_update["description"] is not None:
                project["description"] = project_update["description"]

            return project

    raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def project_delete(project_id: int):
    for index, project in enumerate(projects):
        if project["id"] == project_id:
            project.pop(index)
            return 
        
    raise HTTPException(status_code=404, detail="Project not found")
