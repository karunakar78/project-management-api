from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    # model_config = ConfigDict(extra="forbid")
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
