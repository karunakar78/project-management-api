from fastapi import FastAPI

app = FastAPI()

projects = []

@app.get("/")
def root():
    return {"message": "Project Management API"}


@app.get("/projects")
def get_projects():
    return projects


@app.post("/projects")
def create_projects():
    project = {
        "id": 1,
        "name": "My first project",
        "description": "This is my first project in FastAPI",
    }

    projects.append(project)

    return project