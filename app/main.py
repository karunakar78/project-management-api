from fastapi import FastAPI

from app.database import Base, engine
from app.models.project import Project
from app.routers.projects import router as project_router


Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Project Management API"
    }


app.include_router(project_router)