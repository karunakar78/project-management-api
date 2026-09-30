from fastapi import FastAPI

app = FastAPI()

projects = []

@app.get("/")
def root():
    return {"message": "Project Management API"}

@app.get("/projects")
def get_projects():
    return projects