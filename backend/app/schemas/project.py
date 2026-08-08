from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProjectBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"


class ProjectCreateSchema(ProjectBaseSchema):
    pass


class ProjectUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectSchema(ProjectBaseSchema):
    id: str
    organization_id: str
    
    model_config = ConfigDict(from_attributes=True)
