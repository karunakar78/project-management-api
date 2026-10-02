from fastapi import FastAPI

from app.routers.projects import APIRouter as project_router

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Project Management API"}


app.include_router(project_router)