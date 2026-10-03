from fastapi import FastAPI

from app.routers.projects import router as project_router

app = FastAPI()


app.include_router(project_router)


@app.get("/")
def root():
    return {"message": "Project Management API"}
