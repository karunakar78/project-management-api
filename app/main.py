from fastapi import FastAPI

from app.database import Base, engine
from app.models.project import Project
from app.routers.projects import router as project_router
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.exceptions import ProjectNotFoundError
from app.routers import users

Base.metadata.create_all(bind=engine)


app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Project Management API"
    }


app.include_router(project_router)
app.include_router(users.router)

@app.exception_handler(ProjectNotFoundError)
async def project_not_found_handler(
    request: Request,
    exc: ProjectNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)}
    )