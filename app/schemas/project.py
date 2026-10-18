from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=1, max_length=300)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("name", "description")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
