from fastapi import APIRouter, HTTPException

from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


projects = []


@router.get("/", response_model=list[ProjectResponse])
def get_projects():
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    for project in projects:
        if project["id"] == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    new_project = {
        "id": len(projects) + 1,
        "name": project.name,
        "description": project.description,
        # "secret": "hello"
    }

    projects.append(new_project)

    return new_project


@router.patch("/{project_id}", response_class=ProjectResponse)
def project_update(project_id: int, project_update: ProjectUpdate):
    for project in projects:
        if project["id"] == project_id:
            if project_update["name"] is not None:
                project["name"] = project_update["name"]

            if project_update["description"] is not None:
                project["description"] = project_update["description"]

            return project

    raise HTTPException(status_code=404, detail="Project not found")


@router.delete("/{project_id}")
def project_delete(project_id: int):
    for index, project in enumerate(projects):
        if project["id"] == project_id:
            project.pop(index)

            return {"message": "Project deleted successfully"}
    raise HTTPException(status_code=404, detail="Project not found")
