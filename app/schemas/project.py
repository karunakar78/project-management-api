from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)

    description: str = Field(min_length=1, max_length=300)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=300)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
