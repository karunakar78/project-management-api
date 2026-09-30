from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

app = FastAPI()

projects = []


class ProjectCreate(BaseModel):
    # model_config = ConfigDict(extra="forbid")
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str


@app.get("/")
def root():
    return {"message": "Project Management API"}


@app.get("/projects", response_model=list[ProjectResponse])
def get_projects():
    return projects


@app.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int):
    for project in projects:
        if project["id"] == project_id:
            return project
    raise HTTPException(
        status_code=404,
        detail="Project not found"
    )


@app.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate):
    new_project = {
        "id": len(projects) + 1,
        "name": project.name,
        "description": project.description,
        # "secret": "hello"
    }

    projects.append(new_project)

    return new_project
